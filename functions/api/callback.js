// OAuth callback for FYHOM Decap CMS. GitHub credentials remain server-side.
// The popup only sends the token to its same-origin FYHOM admin opener.
const cookieClear="fyhom_oauth_state=; Path=/api; Max-Age=0; HttpOnly; Secure; SameSite=Lax";
function showResult({token="",error=""}={}) {
  const authorized=token ? "authorization:github:success:"+JSON.stringify({token})
    : "authorization:github:error:"+JSON.stringify({message:error||"Anmeldung fehlgeschlagen"});
  const safe=JSON.stringify(authorized).replace(/</g,"\\u003c");
  const html=`<!doctype html><html lang="de"><head><meta charset="utf-8">
<title>FYHOM · GitHub-Anmeldung</title></head><body>
<p id="message">GitHub-Anmeldung wird abgeschlossen …</p>
<script>
(function(){
  var opener=window.opener;
  var msg=document.getElementById("message");
  if(!opener){msg.textContent="Das Anmeldefenster wurde nicht vom FYHOM-Admin geöffnet. Bitte den Login erneut im Admin starten.";return}
  var authenticated=${safe};
  var sent=false;
  window.addEventListener("message",function(e){
    if(sent || e.origin!==window.location.origin || e.source!==opener) return;
    sent=true;
    opener.postMessage(authenticated, window.location.origin);
    msg.textContent="Anmeldung abgeschlossen. Sie können dieses Fenster schließen.";
    window.setTimeout(function(){window.close()},350);
  });
  opener.postMessage("authorizing:github",window.location.origin);
  window.setTimeout(function(){
    if(!sent) msg.textContent="Keine Antwort vom FYHOM-Admin. Bitte Pop-ups zulassen und erneut versuchen.";
  },5000);
})();
</script></body></html>`;
  return new Response(html,{status:200,headers:{
    "Content-Type":"text/html; charset=utf-8",
    "Cache-Control":"no-store","Referrer-Policy":"no-referrer",
    "X-Content-Type-Options":"nosniff",
    "Content-Security-Policy":"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'",
    "Set-Cookie":cookieClear
  }});
}
export async function onRequestGet({request,env}) {
  const url=new URL(request.url);
  const expected=/(?:^|;\\s*)fyhom_oauth_state=([a-f0-9]{48})(?:;|$)/.exec(request.headers.get("Cookie")||"")?.[1];
  const state=url.searchParams.get("state");
  if(!state || !expected || state!==expected) return showResult({error:"Anmeldesitzung abgelaufen oder ungültig. Bitte erneut anmelden."});
  if(url.searchParams.get("error")) return showResult({error:"GitHub-Zugriff wurde nicht bestätigt."});
  const code=url.searchParams.get("code");
  if(!code || !env.GITHUB_CLIENT_ID || !env.GITHUB_CLIENT_SECRET)
    return showResult({error:"GitHub-OAuth ist noch nicht vollständig eingerichtet."});
  try {
    const res=await fetch("https://github.com/login/oauth/access_token",{
      method:"POST",
      headers:{"Accept":"application/json","Content-Type":"application/x-www-form-urlencoded","User-Agent":"FYHOM-Decap-CMS"},
      body:new URLSearchParams({
        client_id:env.GITHUB_CLIENT_ID,
        client_secret:env.GITHUB_CLIENT_SECRET,
        code,
        redirect_uri:url.origin+"/api/callback"
      })
    });
    if(!res.ok) return showResult({error:"GitHub konnte die Anmeldung nicht abschließen."});
    const data=await res.json();
    const token=typeof data.access_token==="string"?data.access_token:"";
    if(!/^[A-Za-z0-9_\\-]{12,}$/.test(token)) return showResult({error:"GitHub hat kein gültiges Zugriffstoken geliefert. Bitte Callback-URL und OAuth-App prüfen."});
    return showResult({token});
  }catch(e){
    console.error("FYHOM OAuth exchange failed:",String(e).slice(0,120));
    return showResult({error:"GitHub-Anmeldung vorübergehend nicht möglich."});
  }
}
