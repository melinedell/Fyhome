// FYHOM contact endpoint for Cloudflare Pages Functions.
// Server-side only. Configure RESEND_API_KEY and FYHOM_FROM_EMAIL in Cloudflare.
// The sender domain must be verified with Resend. No secrets belong in GitHub.
const TYPES = {
  "fyhom-search": "Immobiliensuchauftrag",
  "fyhom-sell": "Immobilie verkaufen",
  "fyhom-valuation": "Immobilienbewertung",
  "fyhom-contact": "Kontaktanfrage"
};
const VALID_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const reply = (status, message) => Response.json(
  {ok:status===200, message},
  {status, headers:{"Cache-Control":"no-store", "X-Content-Type-Options":"nosniff"}}
);
export async function onRequestPost({request, env}) {
  const origin=request.headers.get("Origin");
  if(origin && new URL(origin).host!==new URL(request.url).host) return reply(403,"Origin not allowed");
  const length=Number(request.headers.get("Content-Length")||"0");
  if(length>16000) return reply(413,"Request too large");
  const type=request.headers.get("Content-Type")||"";
  if(!type.includes("application/x-www-form-urlencoded")) return reply(415,"Invalid content type");
  let body;
  try {
    const raw=await request.text();
    if(raw.length>16000) return reply(413,"Request too large");
    body=new URLSearchParams(raw);
  } catch {return reply(400,"Invalid form");}
  const formType=body.get("form-name");
  if(!Object.hasOwn(TYPES,formType)) return reply(400,"Unknown form");
  if(body.get("bot-field")) return reply(200,"OK");
  if(body.get("consent")!=="on") return reply(400,"Privacy acknowledgement required");
  const email=(body.get("email")||"").trim();
  if(!VALID_EMAIL.test(email)||email.length>254) return reply(400,"Valid email required");
  const name=(body.get("name")||"").trim();
  if(name.length>180) return reply(400,"Invalid name");
  if(!env.RESEND_API_KEY||!env.FYHOM_FROM_EMAIL) {
    return reply(503,"Mail delivery is not configured. Please email info@fyhom.es");
  }
  const rows=[];
  for(const [key,raw] of body.entries()) {
    if(["bot-field","consent","form-name"].includes(key)) continue;
    if(!/^[a-z][a-z0-9_-]{0,40}$/i.test(key)) continue;
    const value=raw.replace(/[\u0000-\u001f\u007f]/g," ").trim().slice(0,2500);
    if(value) rows.push(key+": "+value);
  }
  const textMessage="FYHOM – "+TYPES[formType]+"\n\n"+rows.join("\n")+"\n\nÜbermittelt über "+new URL(request.url).origin;
  try {
    const upstream=await fetch("https://api.resend.com/emails", {
      method:"POST",
      headers:{"Authorization":"Bearer "+env.RESEND_API_KEY,"Content-Type":"application/json"},
      body:JSON.stringify({
        from:env.FYHOM_FROM_EMAIL,
        to:["info@fyhom.es"],
        reply_to:email,
        subject:"FYHOM: "+TYPES[formType],
        text:textMessage
      })
    });
    if(!upstream.ok) {
      console.error("FYHOM email provider rejected submission",upstream.status);
      return reply(502,"Delivery temporarily unavailable");
    }
    return reply(200,"Message accepted for delivery");
  } catch(e) {
    console.error("FYHOM email network error",String(e));
    return reply(502,"Delivery temporarily unavailable");
  }
}
export function onRequestGet() {return reply(405,"Use POST");}
