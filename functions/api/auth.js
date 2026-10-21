// GitHub OAuth entry point for FYHOM Decap CMS on Cloudflare Pages.
// Required Cloudflare Pages secrets: GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET.
// This endpoint uses a fresh, HttpOnly state cookie to prevent OAuth login CSRF.
const respond = (body,status=503) => new Response(body,{
  status,headers:{"Content-Type":"text/plain; charset=utf-8","Cache-Control":"no-store","Referrer-Policy":"no-referrer"}
});
export async function onRequestGet({request,env}) {
  const url=new URL(request.url);
  if(url.searchParams.get("provider") && url.searchParams.get("provider")!=="github") return respond("Unbekannter Anbieter.",400);
  if(!env.GITHUB_CLIENT_ID || !env.GITHUB_CLIENT_SECRET) {
    return respond("FYHOM GitHub-Login ist noch nicht eingerichtet. Bitte die Cloudflare-Umgebungsvariablen GITHUB_CLIENT_ID und GITHUB_CLIENT_SECRET setzen.",503);
  }
  const state=Array.from(crypto.getRandomValues(new Uint8Array(24)),x=>x.toString(16).padStart(2,"0")).join("");
  const authorize=new URL("https://github.com/login/oauth/authorize");
  authorize.searchParams.set("client_id",env.GITHUB_CLIENT_ID);
  authorize.searchParams.set("redirect_uri",url.origin+"/api/callback");
  authorize.searchParams.set("scope","public_repo");
  authorize.searchParams.set("state",state);
  return new Response(null,{
    status:302,
    headers:{
      "Location":authorize.toString(),
      "Set-Cookie":"fyhom_oauth_state="+state+"; Path=/api; Max-Age=600; HttpOnly; Secure; SameSite=Lax",
      "Cache-Control":"no-store",
      "Referrer-Policy":"no-referrer",
      "X-Content-Type-Options":"nosniff"
    }
  });
}
