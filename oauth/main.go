package main

import (
	"crypto/rand"
	"crypto/sha256"
	"embed"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

//go:embed static/*
var staticFS embed.FS

const (
	clientAddr = "localhost:8000"
	authAddr   = "localhost:9000"
	apiAddr    = "localhost:7000"

	demoEmail    = "demo@example.com"
	demoPassword = "password123"
)

type Demo struct {
	mu          sync.RWMutex
	sessions    map[string]*FlowSession
	authCodes   map[string]*AuthCode
	accessToken map[string]*AccessToken
}

type FlowSession struct {
	SessionID     string         `json:"session_id"`
	CurrentStep   string         `json:"current_step"`
	State         string         `json:"state"`
	CodeVerifier  string         `json:"code_verifier"`
	CodeChallenge string         `json:"code_challenge"`
	ChallengeMeth string         `json:"code_challenge_method"`
	AuthCode      string         `json:"auth_code"`
	AccessToken   string         `json:"access_token"`
	TokenType     string         `json:"token_type"`
	ResourceData  map[string]any `json:"resource_data,omitempty"`
	Error         string         `json:"error,omitempty"`
	Events        []FlowEvent    `json:"events"`
	UpdatedAt     time.Time      `json:"updated_at"`
}

type FlowEvent struct {
	Time        string `json:"time"`
	Step        string `json:"step"`
	Actor       string `json:"actor"`
	Title       string `json:"title"`
	Method      string `json:"method,omitempty"`
	URL         string `json:"url,omitempty"`
	Status      int    `json:"status,omitempty"`
	Request     string `json:"request,omitempty"`
	Response    string `json:"response,omitempty"`
	Description string `json:"description,omitempty"`
}

type AuthCode struct {
	Code               string
	SessionID          string
	ClientID           string
	RedirectURI        string
	CodeChallenge      string
	CodeChallengeMeth  string
	AuthenticatedEmail string
	ExpiresAt          time.Time
}

type AccessToken struct {
	Token     string
	SessionID string
	Email     string
	ExpiresAt time.Time
}

type loginPageData struct {
	SessionID           string
	ClientID            string
	RedirectURI         string
	State               string
	CodeChallenge       string
	CodeChallengeMethod string
	Error               string
	DemoEmail           string
	DemoPassword        string
}

func main() {
	demo := &Demo{
		sessions:    map[string]*FlowSession{},
		authCodes:   map[string]*AuthCode{},
		accessToken: map[string]*AccessToken{},
	}

	indexHTML, err := template.ParseFS(staticFS, "static/index.html")
	if err != nil {
		log.Fatalf("parse index template: %v", err)
	}

	clientMux := http.NewServeMux()
	clientMux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if err := indexHTML.Execute(w, map[string]string{
			"ClientBaseURL": "http://" + clientAddr,
			"AuthBaseURL":   "http://" + authAddr,
			"APIBaseURL":    "http://" + apiAddr,
		}); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
	})
	clientMux.HandleFunc("/api/start", demo.handleStart)
	clientMux.HandleFunc("/api/state", demo.handleState)
	clientMux.HandleFunc("/callback", demo.handleCallback)

	authMux := http.NewServeMux()
	authMux.HandleFunc("/authorize", demo.handleAuthorize)
	authMux.HandleFunc("/login", demo.handleLogin)
	authMux.HandleFunc("/token", demo.handleToken)

	apiMux := http.NewServeMux()
	apiMux.HandleFunc("/userinfo", demo.handleUserInfo)

	go runServer(clientAddr, "client application", clientMux)
	go runServer(authAddr, "authorization server", authMux)
	runServer(apiAddr, "resource server", apiMux)
}

func runServer(addr, name string, handler http.Handler) {
	srv := &http.Server{
		Addr:              addr,
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Printf("%s listening on http://%s", name, addr)
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("%s failed: %v", name, err)
	}
}

func (d *Demo) handleStart(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	sessionID := randToken(16)
	state := randToken(16)
	codeVerifier := randToken(32)
	codeChallenge := pkceChallenge(codeVerifier)
	redirectURI := "http://" + clientAddr + "/callback"

	authorizeURL := fmt.Sprintf(
		"http://%s/authorize?response_type=code&client_id=demo-client&redirect_uri=%s&scope=openid%%20profile&state=%s&code_challenge=%s&code_challenge_method=S256&session_id=%s",
		authAddr,
		url.QueryEscape(redirectURI),
		url.QueryEscape(state),
		url.QueryEscape(codeChallenge),
		url.QueryEscape(sessionID),
	)

	session := &FlowSession{
		SessionID:     sessionID,
		CurrentStep:   "client_prepared_authorization_request",
		State:         state,
		CodeVerifier:  codeVerifier,
		CodeChallenge: codeChallenge,
		ChallengeMeth: "S256",
		Events:        []FlowEvent{},
		UpdatedAt:     time.Now(),
	}

	d.mu.Lock()
	d.sessions[sessionID] = session
	d.mu.Unlock()

	d.addEvent(sessionID, FlowEvent{
		Time:    time.Now().Format(time.RFC3339),
		Step:    "1",
		Actor:   "client",
		Title:   "Client generated PKCE material",
		Method:  "LOCAL",
		URL:     "Browser -> Client App",
		Request: prettyJSON(map[string]any{"action": "Generate state, code_verifier, and code_challenge"}),
		Response: prettyJSON(map[string]any{
			"state":                 state,
			"code_verifier":         codeVerifier,
			"code_challenge":        codeChallenge,
			"code_challenge_method": "S256",
		}),
		Description: "The client application creates a random code_verifier, hashes it to create the code_challenge, and stores both with the CSRF state.",
	})

	writeJSON(w, map[string]any{
		"session_id":     sessionID,
		"authorize_url":  authorizeURL,
		"redirect_uri":   redirectURI,
		"code_verifier":  codeVerifier,
		"code_challenge": codeChallenge,
		"state":          state,
	})
}

func (d *Demo) handleState(w http.ResponseWriter, r *http.Request) {
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		http.Error(w, "missing session_id", http.StatusBadRequest)
		return
	}

	d.mu.RLock()
	session, ok := d.sessions[sessionID]
	d.mu.RUnlock()
	if !ok {
		http.Error(w, "unknown session", http.StatusNotFound)
		return
	}
	writeJSON(w, session)
}

func (d *Demo) handleAuthorize(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query()
	sessionID := query.Get("session_id")
	if sessionID == "" {
		http.Error(w, "missing session_id", http.StatusBadRequest)
		return
	}

	d.updateStep(sessionID, "authorization_server_received_authorize_request")
	d.addEvent(sessionID, FlowEvent{
		Time:        time.Now().Format(time.RFC3339),
		Step:        "2",
		Actor:       "authorization-server",
		Title:       "Authorization request arrived",
		Method:      http.MethodGet,
		URL:         r.URL.String(),
		Status:      http.StatusOK,
		Request:     prettyJSON(queryToMap(query)),
		Response:    "Rendered login form for the resource owner.",
		Description: "The authorization server receives the authorization request containing client_id, redirect_uri, state, and PKCE code_challenge.",
	})

	data := loginPageData{
		SessionID:           sessionID,
		ClientID:            query.Get("client_id"),
		RedirectURI:         query.Get("redirect_uri"),
		State:               query.Get("state"),
		CodeChallenge:       query.Get("code_challenge"),
		CodeChallengeMethod: query.Get("code_challenge_method"),
		DemoEmail:           demoEmail,
		DemoPassword:        demoPassword,
	}

	tmpl := template.Must(template.New("login").Parse(loginPageHTML))
	if err := tmpl.Execute(w, data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (d *Demo) handleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if err := r.ParseForm(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	sessionID := r.FormValue("session_id")
	email := r.FormValue("email")
	password := r.FormValue("password")

	d.updateStep(sessionID, "resource_owner_authentication")

	if email != demoEmail || password != demoPassword {
		d.setError(sessionID, "authorization server rejected email/password")
		d.addEvent(sessionID, FlowEvent{
			Time:        time.Now().Format(time.RFC3339),
			Step:        "3",
			Actor:       "authorization-server",
			Title:       "Login failed",
			Method:      http.MethodPost,
			URL:         "/login",
			Status:      http.StatusUnauthorized,
			Request:     prettyJSON(formToMap(r.Form)),
			Response:    prettyJSON(map[string]string{"error": "invalid_credentials"}),
			Description: "The dummy authorization server checks a hard-coded email/password pair.",
		})
		w.WriteHeader(http.StatusUnauthorized)
		_, _ = io.WriteString(w, "<p>Invalid credentials. Use demo@example.com / password123.</p><p><a href=\"javascript:history.back()\">Back</a></p>")
		return
	}

	code := "code-" + randToken(10)
	authCode := &AuthCode{
		Code:               code,
		SessionID:          sessionID,
		ClientID:           r.FormValue("client_id"),
		RedirectURI:        r.FormValue("redirect_uri"),
		CodeChallenge:      r.FormValue("code_challenge"),
		CodeChallengeMeth:  r.FormValue("code_challenge_method"),
		AuthenticatedEmail: email,
		ExpiresAt:          time.Now().Add(2 * time.Minute),
	}

	d.mu.Lock()
	d.authCodes[code] = authCode
	if session, ok := d.sessions[sessionID]; ok {
		session.AuthCode = code
		session.CurrentStep = "authorization_code_issued"
		session.UpdatedAt = time.Now()
	}
	d.mu.Unlock()

	redirectURI, _ := url.Parse(r.FormValue("redirect_uri"))
	params := redirectURI.Query()
	params.Set("code", code)
	params.Set("state", r.FormValue("state"))
	params.Set("session_id", sessionID)
	redirectURI.RawQuery = params.Encode()

	d.addEvent(sessionID, FlowEvent{
		Time:   time.Now().Format(time.RFC3339),
		Step:   "3",
		Actor:  "authorization-server",
		Title:  "Authorization code issued after login",
		Method: http.MethodPost,
		URL:    "/login",
		Status: http.StatusFound,
		Request: prettyJSON(map[string]any{
			"email":                 email,
			"client_id":             r.FormValue("client_id"),
			"redirect_uri":          r.FormValue("redirect_uri"),
			"state":                 r.FormValue("state"),
			"code_challenge":        r.FormValue("code_challenge"),
			"code_challenge_method": r.FormValue("code_challenge_method"),
		}),
		Response: prettyJSON(map[string]string{
			"authorization_code": code,
			"redirect_to":        redirectURI.String(),
		}),
		Description: "After authenticating the user, the authorization server redirects back to the client with an authorization code and the original state.",
	})

	http.Redirect(w, r, redirectURI.String(), http.StatusFound)
}

func (d *Demo) handleCallback(w http.ResponseWriter, r *http.Request) {
	sessionID := r.URL.Query().Get("session_id")
	code := r.URL.Query().Get("code")
	returnedState := r.URL.Query().Get("state")

	d.addEvent(sessionID, FlowEvent{
		Time:        time.Now().Format(time.RFC3339),
		Step:        "4",
		Actor:       "client",
		Title:       "Client received callback",
		Method:      http.MethodGet,
		URL:         r.URL.String(),
		Status:      http.StatusOK,
		Request:     prettyJSON(queryToMap(r.URL.Query())),
		Response:    "Client is validating the state and exchanging the code.",
		Description: "The redirect returns the authorization code to the client. The client must verify the state before using the code.",
	})

	d.mu.RLock()
	session, ok := d.sessions[sessionID]
	d.mu.RUnlock()
	if !ok {
		http.Error(w, "unknown session", http.StatusBadRequest)
		return
	}
	if session.State != returnedState {
		d.setError(sessionID, "state mismatch on callback")
		http.Error(w, "invalid state", http.StatusBadRequest)
		return
	}

	tokenEndpoint := "http://" + authAddr + "/token"
	form := url.Values{}
	form.Set("grant_type", "authorization_code")
	form.Set("client_id", "demo-client")
	form.Set("code", code)
	form.Set("redirect_uri", "http://"+clientAddr+"/callback")
	form.Set("code_verifier", session.CodeVerifier)

	req, _ := http.NewRequestWithContext(r.Context(), http.MethodPost, tokenEndpoint, strings.NewReader(form.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		d.setError(sessionID, "token request failed: "+err.Error())
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	tokenBody, _ := io.ReadAll(resp.Body)
	d.addEvent(sessionID, FlowEvent{
		Time:        time.Now().Format(time.RFC3339),
		Step:        "6",
		Actor:       "client -> authorization-server",
		Title:       "Client exchanged code for access token",
		Method:      http.MethodPost,
		URL:         tokenEndpoint,
		Status:      resp.StatusCode,
		Request:     prettyJSON(formToMap(form)),
		Response:    prettyResponse(tokenBody),
		Description: "PKCE protection happens here: the client submits the original code_verifier and the authorization server recomputes the code_challenge to validate it.",
	})

	if resp.StatusCode != http.StatusOK {
		d.setError(sessionID, "token exchange failed")
		http.Error(w, "token exchange failed", http.StatusBadGateway)
		return
	}

	var tokenResp struct {
		AccessToken string `json:"access_token"`
		TokenType   string `json:"token_type"`
		ExpiresIn   int    `json:"expires_in"`
	}
	if err := json.Unmarshal(tokenBody, &tokenResp); err != nil {
		d.setError(sessionID, "invalid token response")
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}

	d.mu.Lock()
	session.AccessToken = tokenResp.AccessToken
	session.TokenType = tokenResp.TokenType
	session.CurrentStep = "access_token_received"
	session.UpdatedAt = time.Now()
	d.mu.Unlock()

	resourceURL := "http://" + apiAddr + "/userinfo"
	resourceReq, _ := http.NewRequestWithContext(r.Context(), http.MethodGet, resourceURL, nil)
	resourceReq.Header.Set("Authorization", "Bearer "+tokenResp.AccessToken)
	resourceResp, err := http.DefaultClient.Do(resourceReq)
	if err != nil {
		d.setError(sessionID, "resource request failed: "+err.Error())
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}
	defer resourceResp.Body.Close()

	resourceBody, _ := io.ReadAll(resourceResp.Body)
	var resourceData map[string]any
	_ = json.Unmarshal(resourceBody, &resourceData)

	d.mu.Lock()
	session.ResourceData = resourceData
	session.CurrentStep = "resource_response_received"
	session.UpdatedAt = time.Now()
	d.mu.Unlock()

	d.addEvent(sessionID, FlowEvent{
		Time:        time.Now().Format(time.RFC3339),
		Step:        "7",
		Actor:       "client -> resource-server",
		Title:       "Client called protected resource with bearer token",
		Method:      http.MethodGet,
		URL:         resourceURL,
		Status:      resourceResp.StatusCode,
		Request:     prettyJSON(map[string]string{"Authorization": "Bearer " + tokenResp.AccessToken}),
		Response:    prettyResponse(resourceBody),
		Description: "The access token is used to call the resource server. In this demo the resource server returns dummy profile data.",
	})

	http.Redirect(w, r, "/?session_id="+url.QueryEscape(sessionID), http.StatusFound)
}

func (d *Demo) handleToken(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if err := r.ParseForm(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	code := r.FormValue("code")
	codeVerifier := r.FormValue("code_verifier")

	d.mu.RLock()
	authCode, ok := d.authCodes[code]
	d.mu.RUnlock()
	if !ok || time.Now().After(authCode.ExpiresAt) {
		writeJSONStatus(w, http.StatusBadRequest, map[string]string{"error": "invalid_grant"})
		return
	}

	if authCode.CodeChallengeMeth != "S256" || pkceChallenge(codeVerifier) != authCode.CodeChallenge {
		d.setError(authCode.SessionID, "pkce verification failed")
		d.addEvent(authCode.SessionID, FlowEvent{
			Time:        time.Now().Format(time.RFC3339),
			Step:        "5",
			Actor:       "authorization-server",
			Title:       "PKCE verification failed",
			Method:      http.MethodPost,
			URL:         "/token",
			Status:      http.StatusBadRequest,
			Request:     prettyJSON(formToMap(r.Form)),
			Response:    prettyJSON(map[string]string{"error": "invalid_grant"}),
			Description: "The recomputed SHA-256 hash of the code_verifier did not match the stored code_challenge.",
		})
		writeJSONStatus(w, http.StatusBadRequest, map[string]string{"error": "invalid_grant", "error_description": "pkce_verification_failed"})
		return
	}

	token := "atk-" + randToken(12)
	d.mu.Lock()
	d.accessToken[token] = &AccessToken{
		Token:     token,
		SessionID: authCode.SessionID,
		Email:     authCode.AuthenticatedEmail,
		ExpiresAt: time.Now().Add(15 * time.Minute),
	}
	delete(d.authCodes, code)
	if session, ok := d.sessions[authCode.SessionID]; ok {
		session.CurrentStep = "authorization_server_issued_access_token"
		session.UpdatedAt = time.Now()
	}
	d.mu.Unlock()

	response := map[string]any{
		"access_token": token,
		"token_type":   "Bearer",
		"expires_in":   900,
	}
	d.addEvent(authCode.SessionID, FlowEvent{
		Time:        time.Now().Format(time.RFC3339),
		Step:        "5",
		Actor:       "authorization-server",
		Title:       "Authorization server verified PKCE and issued access token",
		Method:      http.MethodPost,
		URL:         "/token",
		Status:      http.StatusOK,
		Request:     prettyJSON(formToMap(r.Form)),
		Response:    prettyJSON(response),
		Description: "The token endpoint verifies the authorization code, redirect_uri, and PKCE code_verifier before minting a bearer access token.",
	})
	writeJSON(w, response)
}

func (d *Demo) handleUserInfo(w http.ResponseWriter, r *http.Request) {
	authz := strings.TrimSpace(r.Header.Get("Authorization"))
	if !strings.HasPrefix(authz, "Bearer ") {
		writeJSONStatus(w, http.StatusUnauthorized, map[string]string{"error": "missing_bearer_token"})
		return
	}
	token := strings.TrimPrefix(authz, "Bearer ")

	d.mu.RLock()
	stored, ok := d.accessToken[token]
	d.mu.RUnlock()
	if !ok || time.Now().After(stored.ExpiresAt) {
		writeJSONStatus(w, http.StatusUnauthorized, map[string]string{"error": "invalid_token"})
		return
	}

	writeJSON(w, map[string]any{
		"sub":          "user-123",
		"email":        stored.Email,
		"name":         "Demo User",
		"issued_for":   stored.SessionID,
		"resource":     "dummy-profile-api",
		"access_token": token,
	})
}

func (d *Demo) addEvent(sessionID string, event FlowEvent) {
	d.mu.Lock()
	defer d.mu.Unlock()
	session, ok := d.sessions[sessionID]
	if !ok {
		return
	}
	session.Events = append(session.Events, event)
	session.UpdatedAt = time.Now()
}

func (d *Demo) updateStep(sessionID, step string) {
	d.mu.Lock()
	defer d.mu.Unlock()
	if session, ok := d.sessions[sessionID]; ok {
		session.CurrentStep = step
		session.UpdatedAt = time.Now()
	}
}

func (d *Demo) setError(sessionID, message string) {
	d.mu.Lock()
	defer d.mu.Unlock()
	if session, ok := d.sessions[sessionID]; ok {
		session.Error = message
		session.UpdatedAt = time.Now()
	}
}

func writeJSON(w http.ResponseWriter, v any) {
	writeJSONStatus(w, http.StatusOK, v)
}

func writeJSONStatus(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func randToken(n int) string {
	buf := make([]byte, n)
	if _, err := rand.Read(buf); err != nil {
		panic(err)
	}
	return hex.EncodeToString(buf)
}

func pkceChallenge(verifier string) string {
	sum := sha256.Sum256([]byte(verifier))
	return strings.TrimRight(base64.URLEncoding.EncodeToString(sum[:]), "=")
}

func prettyJSON(v any) string {
	buf, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Sprintf("%v", v)
	}
	return string(buf)
}

func prettyResponse(data []byte) string {
	var parsed any
	if err := json.Unmarshal(data, &parsed); err == nil {
		return prettyJSON(parsed)
	}
	return string(data)
}

func queryToMap(values url.Values) map[string]string {
	result := make(map[string]string, len(values))
	for k := range values {
		result[k] = values.Get(k)
	}
	return result
}

func formToMap(values url.Values) map[string]string {
	return queryToMap(values)
}

var loginPageHTML = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Dummy Authorization Server</title>
  <style>
    :root {
      --bg: #f4efe6;
      --card: #fff9f1;
      --ink: #1d2433;
      --muted: #5c677a;
      --accent: #a84b2f;
      --border: #d7c7b0;
    }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, #f7d8b7 0, transparent 28%),
        linear-gradient(135deg, #f7f1e6, #efe5d3);
      color: var(--ink);
    }
    .wrap {
      max-width: 920px;
      margin: 40px auto;
      padding: 24px;
    }
    .grid {
      display: grid;
      gap: 20px;
      grid-template-columns: 1.2fr 1fr;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 18px 50px rgba(70, 50, 20, 0.08);
    }
    label, input, button {
      display: block;
      width: 100%;
      font-size: 16px;
    }
    input {
      margin-top: 6px;
      margin-bottom: 16px;
      padding: 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      box-sizing: border-box;
    }
    button {
      padding: 14px;
      border: 0;
      border-radius: 999px;
      background: var(--accent);
      color: white;
      cursor: pointer;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #2a2f3a;
      color: #f1f3f6;
      padding: 14px;
      border-radius: 12px;
      font-size: 13px;
    }
    .meta {
      color: var(--muted);
      font-size: 14px;
    }
    @media (max-width: 840px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="grid">
      <section class="card">
        <p class="meta">Dummy Authorization Server</p>
        <h1>Sign in to continue</h1>
        <p>Use the demo credentials below. This page is deliberately simple so the OAuth redirect and PKCE parameters remain visible.</p>
        <form method="post" action="/login">
          <input type="hidden" name="session_id" value="{{.SessionID}}" />
          <input type="hidden" name="client_id" value="{{.ClientID}}" />
          <input type="hidden" name="redirect_uri" value="{{.RedirectURI}}" />
          <input type="hidden" name="state" value="{{.State}}" />
          <input type="hidden" name="code_challenge" value="{{.CodeChallenge}}" />
          <input type="hidden" name="code_challenge_method" value="{{.CodeChallengeMethod}}" />
          <label>Email</label>
          <input name="email" type="email" value="{{.DemoEmail}}" />
          <label>Password</label>
          <input name="password" type="password" value="{{.DemoPassword}}" />
          <button type="submit">Approve and issue authorization code</button>
        </form>
      </section>
      <aside class="card">
        <p class="meta">Incoming request metadata</p>
        <pre>{
  "client_id": "{{.ClientID}}",
  "redirect_uri": "{{.RedirectURI}}",
  "state": "{{.State}}",
  "code_challenge_method": "{{.CodeChallengeMethod}}",
  "code_challenge": "{{.CodeChallenge}}",
  "demo_login_email": "{{.DemoEmail}}",
  "demo_login_password": "{{.DemoPassword}}"
}</pre>
      </aside>
    </div>
  </div>
</body>
</html>
`
