from flask import Flask, request, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
import os, re, requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ngo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@hopefoundation.org')

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

SUPPORTED_CRYPTO_METHODS = ['bitcoin', 'ethereum', 'sol', 'bnb', 'usdt', 'xrp']

# ------------------------------------------------------------------
# Conservation Fee Price List (Static Reference Data)
# Based on provided fee structure document.
# Amounts for Kenyan / E.A. residents are in KES; Non-resident amounts in USD.
# "Other Activities" fees are surcharges that apply in addition to the base conservation fees.
# ------------------------------------------------------------------
CONSERVATION_PRICE_LIST = {
    'kenyan_ea_citizens': {
        'adult': {'amount': 200, 'currency': 'KES'},
        'child_student': {'amount': 150, 'currency': 'KES'}
    },
    'non_residents': {
        'adult': {'amount': 10, 'currency': 'USD'},
        'child_student': {'amount': 6, 'currency': 'USD'}
    },
    'other_activities': {
        'research': {'amount': 10000, 'currency': 'KES', 'note': 'plus conservation fees'},
        'filming_lt_10_crews': {'amount': 20000, 'currency': 'KES', 'note': 'plus conservation fees'},
        'filming_gt_10_crews': {'amount': 30000, 'currency': 'KES', 'note': 'plus conservation fees'}
    },
    'meta': {
        'disclaimer': 'Activity fees are charged in addition to the standard per-person conservation fees.',
        'last_updated': '2025-08-28'
    }
}

# ------------------------------------------------------------------
# Embedded Frontend (Single Page App-like) – served at '/'
# Provides UI for: Auth (register/login), Donation, Conservation Fee,
# Price List + Group Estimator, Contact, Newsletter, Dashboard.
# NOTE: For production, move this into templates/static assets.
# ------------------------------------------------------------------
FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'/>
    <meta name='viewport' content='width=device-width,initial-scale=1'/>
    <title>Hope Foundation Portal</title>
    <style>
        :root { --bg:#f5f7fa; --panel:#ffffff; --border:#d9e2ec; --primary:#1663c7; --accent:#0d9157; --danger:#c73629; --warn:#c77f16; --text:#1f2d3d; --radius:12px; }
        * { box-sizing:border-box; }
        body { margin:0; font-family:system-ui, Arial, sans-serif; background:var(--bg); color:var(--text); line-height:1.4; }
        header { background:linear-gradient(90deg,#0d9157,#1663c7); color:#fff; padding:1.1rem 1rem 1rem; position:sticky; top:0; z-index:10; }
        header h1 { margin:0 0 .2rem; font-size:1.35rem; }
        nav { display:flex; flex-wrap:wrap; gap:.5rem; }
        nav a { color:#fff; text-decoration:none; font-size:.7rem; letter-spacing:.75px; text-transform:uppercase; padding:.45rem .7rem; border:1px solid rgba(255,255,255,.35); border-radius:999px; transition:.18s background; backdrop-filter:blur(6px); }
        nav a:hover { background:rgba(255,255,255,.18); }
        main { max-width:1250px; margin:1.25rem auto 4rem; padding:0 1rem; display:grid; gap:1.25rem; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); }
        section { background:var(--panel); border:1px solid var(--border); border-radius:var(--radius); padding:1rem 1.15rem 1.25rem; position:relative; box-shadow:0 2px 4px rgba(0,0,0,0.04); }
        section h2 { margin:.1rem 0 .65rem; font-size:1.05rem; }
        form { display:grid; gap:.55rem; margin-top:.25rem; }
        label { font-size:.66rem; font-weight:600; letter-spacing:.6px; text-transform:uppercase; display:block; margin-bottom:2px; }
        input[type=text], input[type=password], input[type=email], input[type=number], select, textarea { width:100%; padding:.55rem .6rem; border:1px solid var(--border); border-radius:8px; font-size:.8rem; background:#fff; resize:vertical; min-height:38px; }
        textarea { min-height:78px; }
        input:focus, textarea:focus, select:focus { outline:2px solid var(--primary); border-color:var(--primary); }
        button { cursor:pointer; border:none; background:var(--primary); color:#fff; font-weight:600; letter-spacing:.5px; font-size:.7rem; padding:.6rem .9rem; border-radius:9px; text-transform:uppercase; display:inline-flex; align-items:center; gap:.4rem; }
        button.secondary { background:var(--accent); }
        button.outline { background:#fff; color:var(--primary); border:1px solid var(--primary); }
        button.danger { background:var(--danger); }
        button:disabled { opacity:.5; cursor:not-allowed; }
        .row2 { display:grid; gap:.55rem; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); }
        .small-note { font-size:.65rem; color:#4d6172; margin-top:.2rem; }
        .status { font-size:.68rem; margin-top:.4rem; padding:.45rem .6rem; border-radius:8px; background:#f0f6ff; border:1px solid #d0e3f9; display:none; }
        .status.error { background:#ffe9e7; border-color:#ffc7c2; color:#7b2318; }
        .status.success { background:#e7f9ef; border-color:#b9eccd; color:#0d6737; }
        table { width:100%; border-collapse:collapse; font-size:.72rem; }
        th,td { padding:.45rem .5rem; border-bottom:1px solid var(--border); text-align:left; }
        th { background:#eef3f9; font-weight:600; font-size:.67rem; letter-spacing:.5px; text-transform:uppercase; }
        .pill { display:inline-block; padding:2px 7px; border-radius:999px; background:#eef3f9; font-size:.6rem; letter-spacing:.5px; text-transform:uppercase; }
        .flex { display:flex; gap:.5rem; flex-wrap:wrap; align-items:center; }
        .grid-mini { display:grid; gap:.4rem; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); margin:.4rem 0 .6rem; }
        .muted { color:#5a6a78; font-size:.65rem; }
        pre { background:#0e11171a; padding:.75rem .9rem; border-radius:9px; font-size:.62rem; overflow:auto; max-height:260px; }
        footer { text-align:center; padding:2rem 1rem 3rem; font-size:.65rem; color:#5a6a78; grid-column:1/-1; }
        .badge { background:#fff5d6; color:#856103; padding:2px 6px; border-radius:6px; font-size:.6rem; margin-left:4px; }
        .inline { display:inline-flex; align-items:center; gap:.4rem; }
        .hidden { display:none !important; }
        .dash-cards { display:grid; gap:.55rem; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); margin-bottom:.6rem; }
        .metric { background:#f0f6ff; border:1px solid #d0e3f9; padding:.6rem .55rem; border-radius:10px; }
        .metric h3 { margin:0 0 .25rem; font-size:.65rem; letter-spacing:.5px; text-transform:uppercase; color:#305170; }
        .metric .val { font-size:.95rem; font-weight:600; }
        .tag { background:#eef3f9; padding:2px 8px; border-radius:999px; font-size:.6rem; text-transform:uppercase; letter-spacing:.5px; }
        .group { border:1px solid var(--border); padding:.6rem .65rem .75rem; border-radius:9px; margin-bottom:.5rem; background:#fafcff; }
        details { margin:.4rem 0 .2rem; }
        summary { cursor:pointer; font-size:.7rem; font-weight:600; letter-spacing:.5px; }
    </style>
</head>
<body>
    <header>
        <h1>Hope Foundation Portal</h1>
        <nav>
            <a href='#auth'>Auth</a>
            <a href='#donate'>Donate</a>
            <a href='#fee'>Conservation Fee</a>
            <a href='#prices'>Prices</a>
            <a href='#contact'>Contact</a>
            <a href='#newsletter'>Newsletter</a>
            <a href='#dashboard'>Dashboard</a>
        </nav>
    </header>
    <main>
        <section id='auth'>
            <h2>Authentication <span class='pill'>Register / Login</span></h2>
            <div class='group'>
                <h3 style='margin:.1rem 0 .35rem;font-size:.8rem;'>Register</h3>
                <form id='registerForm'>
                    <div class='row2'>
                        <div><label>Username</label><input name='username' required/></div>
                        <div><label>Email</label><input name='email' type='email' required/></div>
                        <div><label>Password</label><input name='password' type='password' required/></div>
                        <div><label>First Name</label><input name='first_name' required/></div>
                        <div><label>Last Name</label><input name='last_name' required/></div>
                        <div><label>Phone</label><input name='phone'/></div>
                    </div>
                    <button>Register</button>
                    <div class='status' id='registerStatus'></div>
                </form>
            </div>
            <div class='group'>
                <h3 style='margin:.1rem 0 .35rem;font-size:.8rem;'>Login</h3>
                <form id='loginForm'>
                    <div class='row2'>
                        <div><label>Username or Email</label><input name='login' required/></div>
                        <div><label>Password</label><input name='password' type='password' required/></div>
                    </div>
                    <button>Login</button>
                    <button type='button' class='outline' id='logoutBtn' disabled>Logout</button>
                    <div class='status' id='loginStatus'></div>
                </form>
            </div>
        </section>

        <section id='donate'>
            <h2>Cryptocurrency Donation <span class='pill'>/api/donate</span></h2>
            <form id='donationForm'>
                <div class='row2'>
                    <div><label>Name</label><input name='donorName' required/></div>
                    <div><label>Email</label><input name='donorEmail' type='email' required/></div>
                    <div><label>Phone</label><input name='donorPhone'/></div>
                    <div><label>Amount (USD)</label><input name='amount' type='number' min='1' value='25' required/></div>
                    <div><label>Payment Method</label><select name='paymentMethod' required id='donationCrypto'></select></div>
                    <div><label>Donation Type</label><select name='donationType'><option value='one-time'>One-Time</option><option value='recurring'>Recurring</option></select></div>
                    <div><label>Project</label><input name='projectSelection' placeholder='general'/></div>
                    <div><label>Anonymous?</label><select name='anonymous'><option value='false'>No</option><option value='true'>Yes</option></select></div>
                </div>
                <label>Message</label><textarea name='donorMessage' placeholder='Optional message...'></textarea>
                <label><input type='checkbox' name='newsletter'/> Subscribe to newsletter</label>
                <button>Submit Donation</button>
                <div class='status' id='donationStatus'></div>
            </form>
            <details><summary>Response</summary><pre id='donationResult'></pre></details>
        </section>

        <section id='fee'>
            <h2>Conservation Fee <span class='pill'>/api/conservation/fee</span></h2>
            <form id='feeForm'>
                <div class='row2'>
                    <div><label>Name</label><input name='name' required/></div>
                    <div><label>Email</label><input name='email' type='email' required/></div>
                    <div><label>Country</label><input name='country'/></div>
                    <div><label>ID / Passport No.</label><input name='idNumber'/></div>
                    <div><label>Amount (USD)</label><input name='amount' type='number' min='1' value='10' required/></div>
                    <div><label>Payment Method</label><select name='paymentMethod' required id='feeCrypto'></select></div>
                    <div><label>Phone</label><input name='phone'/></div>
                </div>
                <button>Create Fee</button>
                <div class='status' id='feeStatus'></div>
            </form>
            <details><summary>Response</summary><pre id='feeResult'></pre></details>
            <div style='margin-top:.6rem;'>Verify Receipt Code: <input id='verifyCode' style='max-width:170px;' placeholder='Enter receipt code'/> <button type='button' id='verifyBtn' class='secondary'>Verify</button></div>
            <pre id='verifyResult' style='display:none;'></pre>
        </section>

        <section id='prices'>
            <h2>Conservation Price List <span class='pill'>/api/conservation/prices</span></h2>
            <div id='priceTables' class='flex' style='flex-wrap:wrap;'></div>
            <div class='muted' id='priceMeta'></div>
            <hr style='margin:1rem 0 .9rem;border:none;border-top:1px solid var(--border);'/>
            <h3 style='margin:.1rem 0 .4rem;font-size:.8rem;'>Group Cost Estimator</h3>
            <div class='grid-mini'>
                <div><label>Resident Adults</label><input type='number' id='resAdults' min='0' value='0'/></div>
                <div><label>Resident Children</label><input type='number' id='resChildren' min='0' value='0'/></div>
                <div><label>Non-Res Adults</label><input type='number' id='nrAdults' min='0' value='0'/></div>
                <div><label>Non-Res Children</label><input type='number' id='nrChildren' min='0' value='0'/></div>
                <div><label>Research?</label><select id='research'><option value='0'>No</option><option value='1'>Yes</option></select></div>
                <div><label>Film <10 Crew?</label><select id='filmSmall'><option value='0'>No</option><option value='1'>Yes</option></select></div>
                <div><label>Film >10 Crew?</label><select id='filmLarge'><option value='0'>No</option><option value='1'>Yes</option></select></div>
            </div>
            <div class='status' id='estimateBox' style='display:block;background:#f0f6ff;border-color:#d0e3f9;'></div>
            <details><summary>Raw API Data</summary><pre id='pricesRaw'></pre></details>
        </section>

        <section id='contact'>
            <h2>Contact Us <span class='pill'>/api/contact</span></h2>
            <form id='contactForm'>
                <div class='row2'>
                    <div><label>Name</label><input name='name' required/></div>
                    <div><label>Email</label><input name='email' type='email' required/></div>
                    <div><label>Phone</label><input name='phone'/></div>
                    <div><label>Subject</label><input name='subject' placeholder='General Inquiry'/></div>
                </div>
                <label>Message</label><textarea name='message' required></textarea>
                <label><input type='checkbox' name='newsletter'/> Subscribe to newsletter</label>
                <button>Send Message</button>
                <div class='status' id='contactStatus'></div>
            </form>
        </section>

        <section id='newsletter'>
            <h2>Newsletter <span class='pill'>/api/newsletter</span></h2>
            <form id='newsletterForm' style='display:flex; gap:.55rem; align-items:flex-start; flex-wrap:wrap;'>
                <div style='flex:1 1 220px;'>
                    <label style='margin-bottom:4px;'>Email</label>
                    <input name='email' type='email' required/>
                </div>
                <div style='padding-top:1.2rem;'>
                    <button>Subscribe</button>
                </div>
            </form>
            <div class='status' id='newsletterStatus'></div>
        </section>

        <section id='dashboard'>
            <h2>User Dashboard <span class='pill'>/api/user/dashboard</span></h2>
            <div id='dashContent' class='muted'>Login to view dashboard.</div>
            <details style='margin-top:.6rem;'><summary>Recent Donations Payload</summary><pre id='dashRaw'></pre></details>
        </section>

        <footer>&copy; <span id='year'></span> Hope Foundation • Demo Interface (Embedded)</footer>
    </main>

    <script>
        const yearSpan = document.getElementById('year'); yearSpan.textContent = new Date().getFullYear();
        const cryptos = %s; // Inject list
        function fillSelect(id){ const sel = document.getElementById(id); sel.innerHTML = cryptos.map(c=>`<option value="${c}">${c.toUpperCase()}</option>`).join(''); }
        fillSelect('donationCrypto'); fillSelect('feeCrypto');
        // Helpers
        function formToJSON(form){ const fd = new FormData(form); const o={}; fd.forEach((v,k)=>{ if(o[k]){ if(!Array.isArray(o[k])) o[k]=[o[k]]; o[k].push(v);} else o[k]=v;}); return o; }
        function setStatus(elId,msg,ok){ const el=document.getElementById(elId); el.textContent=msg; el.style.display='block'; el.classList.remove('error','success'); el.classList.add(ok?'success':'error'); }
        async function postJSON(url,data){ return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); }
        // Register
        document.getElementById('registerForm').addEventListener('submit', async e=>{ e.preventDefault(); const data=formToJSON(e.target); setStatus('registerStatus','Submitting...',true); try{ const r=await postJSON('/api/register',data); const j=await r.json(); if(r.ok){ setStatus('registerStatus',j.message||'Registered',true); loadDashboard(); } else setStatus('registerStatus',j.message||'Failed',false);}catch(err){ setStatus('registerStatus',err.message,false);} });
        // Login / Logout
        document.getElementById('loginForm').addEventListener('submit', async e=>{ e.preventDefault(); const data=formToJSON(e.target); setStatus('loginStatus','Logging in...',true); try{ const r=await postJSON('/api/login',data); const j=await r.json(); if(r.ok){ setStatus('loginStatus',j.message||'Logged in',true); document.getElementById('logoutBtn').disabled=false; loadDashboard(); } else setStatus('loginStatus',j.message||'Failed',false);}catch(err){ setStatus('loginStatus',err.message,false);} });
        document.getElementById('logoutBtn').addEventListener('click', async ()=>{ try{ const r=await fetch('/api/logout',{method:'POST'}); if(r.ok){ setStatus('loginStatus','Logged out',true); document.getElementById('logoutBtn').disabled=true; document.getElementById('dashContent').textContent='Login to view dashboard.'; document.getElementById('dashRaw').textContent=''; }}catch{} });
        // Donation
        document.getElementById('donationForm').addEventListener('submit', async e=>{ e.preventDefault(); const data=formToJSON(e.target); if(data.anonymous==='true') data.anonymous=true; setStatus('donationStatus','Submitting...',true); try{ const r=await postJSON('/api/donate',data); const j=await r.json(); document.getElementById('donationResult').textContent=JSON.stringify(j,null,2); if(r.ok){ setStatus('donationStatus',j.message||'Success',true);} else setStatus('donationStatus',j.message||'Failed',false); }catch(err){ setStatus('donationStatus',err.message,false);} });
        // Conservation Fee
        document.getElementById('feeForm').addEventListener('submit', async e=>{ e.preventDefault(); const data=formToJSON(e.target); setStatus('feeStatus','Submitting...',true); try{ const r=await postJSON('/api/conservation/fee',data); const j=await r.json(); document.getElementById('feeResult').textContent=JSON.stringify(j,null,2); if(r.ok){ setStatus('feeStatus',j.message||'Success',true);} else setStatus('feeStatus',j.message||'Failed',false); }catch(err){ setStatus('feeStatus',err.message,false);} });
        document.getElementById('verifyBtn').addEventListener('click', async ()=>{ const code=document.getElementById('verifyCode').value.trim(); if(!code){ return; } const out=document.getElementById('verifyResult'); out.style.display='block'; out.textContent='Verifying...'; try{ const r=await fetch('/api/conservation/verify/'+encodeURIComponent(code)); const j=await r.json(); out.textContent=JSON.stringify(j,null,2);}catch(err){ out.textContent=err.message; }});
        // Contact
        document.getElementById('contactForm').addEventListener('submit', async e=>{ e.preventDefault(); const data=formToJSON(e.target); setStatus('contactStatus','Sending...',true); try{ const r=await postJSON('/api/contact',data); const j=await r.json(); setStatus('contactStatus',j.message||'Sent',r.ok); }catch(err){ setStatus('contactStatus',err.message,false);} });
        // Newsletter
        document.getElementById('newsletterForm').addEventListener('submit', async e=>{ e.preventDefault(); const data=formToJSON(e.target); setStatus('newsletterStatus','Subscribing...',true); try{ const r=await postJSON('/api/newsletter',data); const j=await r.json(); setStatus('newsletterStatus',j.message||'Done',r.ok); }catch(err){ setStatus('newsletterStatus',err.message,false);} });
        // Dashboard
        async function loadDashboard(){ try{ const r=await fetch('/api/user/dashboard'); if(!r.ok){ return; } const j=await r.json(); const d=j.dashboard; const dashContent=document.getElementById('dashContent'); const recent=d.recent_donations || []; let html=`<div class='dash-cards'>`+
            `<div class='metric'><h3>Total Donated</h3><div class='val'>$${d.stats.total_donated.toFixed(2)}</div></div>`+
            `<div class='metric'><h3>Donations</h3><div class='val'>${d.stats.donation_count}</div></div>`+
            `<div class='metric'><h3>Last Donation</h3><div class='val'>${d.stats.last_donation?new Date(d.stats.last_donation).toLocaleDateString():"—"}</div></div>`+
            `</div>`;
            html += `<table><thead><tr><th>Amount</th><th>Project</th><th>Date</th><th>Status</th></tr></thead><tbody>`+recent.map(r=>`<tr><td>$${r.amount}</td><td>${r.project}</td><td>${new Date(r.date).toLocaleDateString()}</td><td>${r.status}</td></tr>`).join('')+`</tbody></table>`;
            dashContent.innerHTML=html; document.getElementById('dashRaw').textContent=JSON.stringify(j,null,2); }catch(err){ /* ignore */ } }
        loadDashboard();
        // Price List + Estimator
        let PRICE_DATA=null; const ids=['resAdults','resChildren','nrAdults','nrChildren','research','filmSmall','filmLarge']; ids.forEach(i=>document.getElementById(i).addEventListener('input',estimate));
        async function loadPrices(){ try{ const r=await fetch('/api/conservation/prices'); const j=await r.json(); if(!r.ok) throw new Error(j.message||'Failed'); PRICE_DATA=j.prices; renderPriceTables(); document.getElementById('pricesRaw').textContent=JSON.stringify(j,null,2); document.getElementById('priceMeta').innerHTML=`${PRICE_DATA.meta.disclaimer}<br><strong>Last Updated:</strong> ${PRICE_DATA.meta.last_updated}`; estimate(); }catch(err){ document.getElementById('priceTables').innerHTML=`<div class='status error' style='display:block;'>${err.message}</div>`; } }
        function renderPriceTables(){ const p=PRICE_DATA; function card(title,rows){ return `<div style='min-width:240px;flex:1 1 260px;'><h3 style='font-size:.8rem;margin:.2rem 0 .45rem;'>${title}</h3><table>${rows}</table></div>`; }
            const res = `<thead><tr><th>Category</th><th>Amount (KES)</th></tr></thead><tbody>`+
                `<tr><td>Adult</td><td>${p.kenyan_ea_citizens.adult.amount.toLocaleString()}</td></tr>`+
                `<tr><td>Child / Student</td><td>${p.kenyan_ea_citizens.child_student.amount.toLocaleString()}</td></tr></tbody>`;
            const non = `<thead><tr><th>Category</th><th>Amount (USD)</th></tr></thead><tbody>`+
                `<tr><td>Adult</td><td>${p.non_residents.adult.amount}</td></tr>`+
                `<tr><td>Child / Student</td><td>${p.non_residents.child_student.amount}</td></tr></tbody>`;
            const act = `<thead><tr><th>Activity</th><th>Fee (KES)</th></tr></thead><tbody>`+
                `<tr><td>Research <span class='badge'>+ base fee</span></td><td>${p.other_activities.research.amount.toLocaleString()}</td></tr>`+
                `<tr><td>Filming <10 crews <span class='badge'>+ base fee</span></td><td>${p.other_activities.filming_lt_10_crews.amount.toLocaleString()}</td></tr>`+
                `<tr><td>Filming >10 crews <span class='badge'>+ base fee</span></td><td>${p.other_activities.filming_gt_10_crews.amount.toLocaleString()}</td></tr></tbody>`;
            document.getElementById('priceTables').innerHTML=[card('Kenyan / E.A. Citizens',res),card('Non-Residents',non),card('Other Activities',act)].join(''); }
        function num(id){ const v=document.getElementById(id).value; return v==''?0:parseInt(v,10)||0; }
        function estimate(){ if(!PRICE_DATA) return; const p=PRICE_DATA; const residentsKES = num('resAdults')*p.kenyan_ea_citizens.adult.amount + num('resChildren')*p.kenyan_ea_citizens.child_student.amount + (num('research')?p.other_activities.research.amount:0) + (num('filmSmall')?p.other_activities.filming_lt_10_crews.amount:0) + (num('filmLarge')?p.other_activities.filming_gt_10_crews.amount:0); const nonUSD = num('nrAdults')*p.non_residents.adult.amount + num('nrChildren')*p.non_residents.child_student.amount; document.getElementById('estimateBox').textContent = `KES Total: ${residentsKES.toLocaleString()} | USD Total: ${nonUSD}`; }
        loadPrices();
    </script>
</body>
</html>""" % SUPPORTED_CRYPTO_METHODS

def get_all_crypto_addresses():
    return {
        'bitcoin': os.getenv('BITCOIN_ADDRESS', 'BITCOIN_ADDRESS_NOT_SET'),
        'ethereum': os.getenv('ETHEREUM_ADDRESS', 'ETHEREUM_ADDRESS_NOT_SET'),
        'sol': os.getenv('SOL_ADDRESS', 'SOL_ADDRESS_NOT_SET'),
        'bnb': os.getenv('BNB_ADDRESS', 'BNB_ADDRESS_NOT_SET'),
        'usdt': os.getenv('USDT_ADDRESS', 'USDT_ADDRESS_NOT_SET'),
        'xrp': os.getenv('XRP_ADDRESS', 'XRP_ADDRESS_NOT_SET'),
    }

# ------------------------------------------------------------------
# Extensions
# ------------------------------------------------------------------
db = SQLAlchemy(app)
mail = Mail(app)

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    payments = db.relationship('Payment', backref='user', lazy=True)
    donations = db.relationship('Donation', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    newsletter = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_method = db.Column(db.String(20), nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100), unique=True)
    reference_code = db.Column(db.String(40), unique=True, index=True)
    gateway_reference = db.Column(db.String(100))
    gateway_response = db.Column(db.Text)
    payment_type = db.Column(db.String(20), default='donation')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=True)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    donation_type = db.Column(db.String(20), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    project = db.Column(db.String(50), default='general')
    message = db.Column(db.Text)
    anonymous = db.Column(db.Boolean, default=False)
    newsletter = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    payment = db.relationship('Payment', backref='donation', uselist=False)

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    project = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    receipt_url = db.Column(db.String(200))
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    allocated_amount = db.Column(db.Float, nullable=False)
    spent_amount = db.Column(db.Float, default=0)
    project = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    goal_amount = db.Column(db.Float, nullable=False)
    raised_amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    project_category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FinancialReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    report_type = db.Column(db.String(30), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer)
    month = db.Column(db.Integer)
    total_income = db.Column(db.Float, default=0)
    total_expenses = db.Column(db.Float, default=0)
    program_expenses = db.Column(db.Float, default=0)
    admin_expenses = db.Column(db.Float, default=0)
    fundraising_expenses = db.Column(db.Float, default=0)
    net_result = db.Column(db.Float, default=0)
    report_data = db.Column(db.Text)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

class ConservationFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payer_name = db.Column(db.String(120), nullable=False)
    payer_email = db.Column(db.String(120), nullable=False)
    payer_phone = db.Column(db.String(30))
    country = db.Column(db.String(60))
    id_number = db.Column(db.String(60))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_method = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100), unique=True)
    receipt_code = db.Column(db.String(40), unique=True, index=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_public_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'receipt_code': self.receipt_code,
            'payer_name': self.payer_name,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------
def validate_email_address(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_phone(phone):
    if not phone:
        return True
    return bool(re.match(r'^\+?[\d\s\-\(\)]{8,}$', phone))

def generate_transaction_id():
    import time, random
    return f"TXN{int(time.time())}{random.randint(10000,99999)}"

def generate_receipt_code(length=10):
    import secrets, string
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_reference_code(payment_type="donation", project_slug=None):
    today = datetime.utcnow()
    year = today.year
    mmdd = today.strftime('%m%d')
    import random, string
    if payment_type == 'conservation_fee':
        seq = (Payment.query.filter(
            Payment.payment_type == 'conservation_fee',
            db.extract('year', Payment.created_at) == year
        ).count() + 1)
        return f"PCBO-{year}-{seq:06d}"
    if project_slug:
        proj_code = re.sub(r'[^A-Za-z0-9]', '', project_slug).upper()[:3] or 'GEN'
        rand4 = ''.join(random.choice(string.digits) for _ in range(4))
        return f"DON-{proj_code}-{mmdd}-{rand4}"
    seq = (Payment.query.filter(
        Payment.payment_type == 'donation',
        db.extract('year', Payment.created_at) == year
    ).count() + 1)
    return f"DON-{year}-{seq:06d}"

def mask_email(email):
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please log in to access this feature.'}), 401
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def send_email(to, subject, template):
    try:
        msg = Message(subject=subject, recipients=[to] if isinstance(to, str) else to, html=template, sender=app.config['MAIL_DEFAULT_SENDER'])
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_discord_notification(donation_data):
    if not DISCORD_WEBHOOK_URL:
        return False
    try:
        embed = {
            "title": "🎉 New Cryptocurrency Donation Received!",
            "description": f"A new donation of ${donation_data['amount']} has been submitted",
            "color": 0x28A745,
            "fields": [
                {"name": "💰 Amount", "value": f"${donation_data['amount']}", "inline": True},
                {"name": "🪙 Cryptocurrency", "value": donation_data['payment_method'].title(), "inline": True},
                {"name": "🎯 Project", "value": donation_data['project'].replace('-', ' ').title(), "inline": True},
                {"name": "👤 Donor", "value": "Anonymous" if donation_data.get('anonymous') else donation_data['donor_name'], "inline": True},
                {"name": "📧 Email", "value": donation_data['donor_email'] if not donation_data.get('anonymous') else "Hidden", "inline": True},
                {"name": "🔗 Transaction ID", "value": donation_data['transaction_id'], "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "footer": {"text": "Hope Foundation Crypto Donations"}
        }
        if donation_data.get('message'):
            msg_val = donation_data['message']
            embed["fields"].append({
                "name": "💌 Message",
                "value": msg_val[:500] + ("..." if len(msg_val) > 500 else ""),
                "inline": False
            })
        resp = requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=8)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")
        return False

# ------------------------------------------------------------------
# Static Routes
# ------------------------------------------------------------------
@app.route('/')
def index():
    return FRONTEND_HTML

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# ------------------------------------------------------------------
# Auth Routes
# ------------------------------------------------------------------
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        for field in ['username','email','password','first_name','last_name']:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field.replace("_"," ").title()} is required.'}), 400
        if not validate_email_address(data['email']):
            return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        if len(data['password']) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters long.'}), 400
        if data.get('phone') and not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': 'Please enter a valid phone number.'}), 400
        existing = User.query.filter((User.username==data['username']) | (User.email==data['email'])).first()
        if existing:
            return jsonify({'success': False, 'message': 'Username or email already exists.'}), 400
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone')
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True, 'message': 'Account created successfully!', 'user': user.to_dict()})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred during registration.'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        if not data.get('login') or not data.get('password'):
            return jsonify({'success': False, 'message': 'Username/email and password are required.'}), 400
        user = User.query.filter((User.username==data['login']) | (User.email==data['login'])).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'success': False, 'message': 'Invalid login credentials.'}), 401
        if not user.is_active:
            return jsonify({'success': False, 'message': 'Account is deactivated.'}), 401
        user.last_login = datetime.utcnow()
        db.session.commit()
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True, 'message': 'Login successful!', 'user': user.to_dict()})
    except Exception:
        return jsonify({'success': False, 'message': 'An error occurred during login.'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully!'})

@app.route('/api/user/profile', methods=['GET'])
@require_login
def get_profile():
    user = get_current_user()
    return jsonify({'success': True, 'user': user.to_dict()})

@app.route('/api/user/profile', methods=['PUT'])
@require_login
def update_profile():
    try:
        user = get_current_user()
        data = request.get_json() or {}
        if data.get('first_name'): user.first_name = data['first_name']
        if data.get('last_name'): user.last_name = data['last_name']
        if data.get('phone') is not None:
            if data['phone'] and not validate_phone(data['phone']):
                return jsonify({'success': False, 'message': 'Please enter a valid phone number.'}), 400
            user.phone = data['phone']
        if data.get('email') and data['email'] != user.email:
            if not validate_email_address(data['email']):
                return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
            existing = User.query.filter(User.email==data['email'], User.id!=user.id).first()
            if existing:
                return jsonify({'success': False, 'message': 'Email already in use.'}), 400
            user.email = data['email']
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully!', 'user': user.to_dict()})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred updating profile.'}), 500

# ------------------------------------------------------------------
# Public Forms
# ------------------------------------------------------------------
@app.route('/api/contact', methods=['POST'])
def contact_form():
    try:
        data = request.get_json() or {}
        if not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({'success': False, 'message': 'Name, email, and message are required.'}), 400
        if not validate_email_address(data['email']):
            return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        if not validate_phone(data.get('phone')):
            return jsonify({'success': False, 'message': 'Please enter a valid phone number.'}), 400
        contact = Contact(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            subject=data.get('subject','General Inquiry'),
            message=data['message'],
            newsletter=data.get('newsletter', False),
            user_id=session.get('user_id')
        )
        db.session.add(contact)
        if data.get('newsletter') and not Newsletter.query.filter_by(email=data['email']).first():
            db.session.add(Newsletter(email=data['email']))
        db.session.commit()
        email_template = f"""
        <h2>Thank you for contacting Hope Foundation!</h2>
        <p>Dear {data['name']},</p>
        <p>We have received your message and will get back to you within 24-48 hours.</p>
        <p><strong>Your message:</strong></p>
        <p>{data['message']}</p>
        <p>Best regards,<br>Hope Foundation Team</p>
        """
        send_email(data['email'], 'Thank you for contacting Hope Foundation', email_template)
        return jsonify({'success': True,'message': 'Thank you for your message! We will get back to you soon.'})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'}), 500

# ------------------------------------------------------------------
# Donation Route
# ------------------------------------------------------------------
@app.route('/api/donate', methods=['POST'])
def donation_form():
    try:
        data = request.get_json() or {}
        if not data.get('donorName') or not data.get('donorEmail'):
            return jsonify({'success': False, 'message': 'Name and email are required.'}), 400
        if not validate_email_address(data['donorEmail']):
            return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        raw = data.get('customAmount') if data.get('amount') == 'custom' else data.get('amount')
        try:
            amount = float(raw)
            if amount <= 0: raise ValueError
        except Exception:
            return jsonify({'success': False, 'message': 'Please enter a valid donation amount.'}), 400
        method = (data.get('paymentMethod') or '').lower()
        if not method:
            return jsonify({'success': False, 'message': 'Please select a payment method.'}), 400
        if method not in SUPPORTED_CRYPTO_METHODS:
            return jsonify({'success': False, 'message': f'Unsupported cryptocurrency. Supported: {", ".join(m.title() for m in SUPPORTED_CRYPTO_METHODS)}'}), 400
        donation = Donation(
            name=data['donorName'],
            email=data['donorEmail'],
            phone=data.get('donorPhone'),
            amount=amount,
            donation_type=data.get('donationType','one-time'),
            payment_method=method,
            project=data.get('projectSelection','general'),
            message=data.get('donorMessage'),
            anonymous=data.get('anonymous', False),
            newsletter=data.get('newsletter', False),
            user_id=session.get('user_id')
        )
        db.session.add(donation)
        db.session.flush()
        transaction_id = generate_transaction_id()
        reference_code = generate_reference_code('donation', data.get('projectSelection'))
        payment = Payment(
            user_id=session.get('user_id'),
            amount=amount,
            payment_method=method,
            transaction_id=transaction_id,
            reference_code=reference_code,
            payment_type='donation',
            description=f"Donation to {data.get('projectSelection','general').replace('-', ' ').title()}",
            donation_id=donation.id
        )
        db.session.add(payment)
        donation.transaction_id = transaction_id
        if data.get('newsletter') and not Newsletter.query.filter_by(email=data['donorEmail']).first():
            db.session.add(Newsletter(email=data['donorEmail']))
        db.session.commit()
        crypto_address = get_all_crypto_addresses().get(method, 'N/A')
        email_template = f"""<h2>Thank you for your cryptocurrency donation!</h2>
<p>Dear {data['donorName']},</p>
<p>Thank you for your {method.title()} donation of ${amount} to Hope Foundation!</p>
<p><strong>Donation Details:</strong></p>
<ul>
  <li>Amount: ${amount}</li>
  <li>Type: {data.get('donationType','one-time').title()}</li>
  <li>Cryptocurrency: {method.title()}</li>
  <li>Project: {data.get('projectSelection','general').replace('-', ' ').title()}</li>
  <li>Transaction ID: {transaction_id}</li>
  <li>Reference Code: {reference_code}</li>
</ul>
<p><strong>To complete your donation, please send the cryptocurrency to:</strong></p>
<p style=\"background:#f8f9fa;padding:15px;border-radius:5px;font-family:monospace;word-break:break-all;\">{crypto_address}</p>
<p><strong>Important:</strong> Please send exactly ${amount} worth of {method.title()} to the address above.</p>
<p>Once your transaction is confirmed on the blockchain, we will process your donation.</p>
<p>Your donation will make a real difference in the lives of those we serve.</p>
<p>A tax-deductible receipt will be sent once the transaction is confirmed.</p>
<p>Best regards,<br>Hope Foundation Team</p>"""
        send_email(data['donorEmail'], f'Complete your {method.title()} donation to Hope Foundation', email_template)
        send_discord_notification({
            'amount': amount,
            'payment_method': method,
            'project': data.get('projectSelection','general'),
            'donor_name': data['donorName'],
            'donor_email': data['donorEmail'],
            'anonymous': data.get('anonymous', False),
            'message': data.get('donorMessage',''),
            'transaction_id': transaction_id
        })
        return jsonify({
            'success': True,
            'message': f'Thank you! Please send ${amount} worth of {method.title()} to complete your donation. Check your email for wallet address details.',
            'amount': amount,
            'paymentMethod': method,
            'transactionId': transaction_id,
            'referenceCode': reference_code,
            'walletAddress': crypto_address,
            'supportedPaymentMethods': SUPPORTED_CRYPTO_METHODS
        })
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'}), 500

# ------------------------------------------------------------------
# Conservation Fee
# ------------------------------------------------------------------
@app.route('/api/conservation/fee', methods=['POST'])
def create_conservation_fee():
    try:
        data = request.get_json() or {}
        for f in ['name','email','amount','paymentMethod']:
            if not data.get(f):
                return jsonify({'success': False, 'message': f'{f} is required.'}), 400
        if not validate_email_address(data['email']):
            return jsonify({'success': False, 'message': 'Invalid email address.'}), 400
        try:
            amount = float(data['amount'])
            if amount <= 0: raise ValueError
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid amount.'}), 400
        payment_method = data['paymentMethod'].lower()
        if payment_method not in SUPPORTED_CRYPTO_METHODS:
            return jsonify({'success': False, 'message': f'Unsupported cryptocurrency. Supported: {", ".join(m.title() for m in SUPPORTED_CRYPTO_METHODS)}'}), 400
        transaction_id = generate_transaction_id()
        receipt_code = generate_receipt_code()
        reference_code = generate_reference_code('conservation_fee')
        payment = Payment(
            user_id=session.get('user_id'),
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            reference_code=reference_code,
            payment_type='conservation_fee',
            description='Conservation Fee'
        )
        db.session.add(payment)
        db.session.flush()
        fee = ConservationFee(
            payer_name=data['name'],
            payer_email=data['email'],
            payer_phone=data.get('phone'),
            country=data.get('country'),
            id_number=data.get('idNumber'),
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            receipt_code=receipt_code,
            payment_id=payment.id
        )
        db.session.add(fee)
        wallet_address = get_all_crypto_addresses().get(payment_method, 'N/A')
        db.session.commit()
        email_html = f"""<h2>Conservation Fee Initiated</h2>
<p>Dear {data['name']},</p>
<p>Thank you for supporting conservation efforts. Please complete your payment using the cryptocurrency details below.</p>
<ul>
  <li><strong>Amount:</strong> ${amount}</li>
  <li><strong>Cryptocurrency:</strong> {payment_method.title()}</li>
  <li><strong>Transaction ID:</strong> {transaction_id}</li>
  <li><strong>Receipt Code:</strong> {receipt_code}</li>
  <li><strong>Reference Code:</strong> {reference_code}</li>
  <li><strong>Status:</strong> Pending Confirmation</li>
</ul>
<p><strong>Send exactly ${amount} worth of {payment_method.title()} to:</strong></p>
<p style='background:#f8f9fa;padding:12px;border-radius:6px;font-family:monospace;'>{wallet_address}</p>
<p>You can later verify this fee at:<br>
<a href=\"{request.host_url.rstrip('/')}/api/conservation/verify/{receipt_code}\">{request.host_url.rstrip('/')}/api/conservation/verify/{receipt_code}</a></p>
<p>Show the receipt code or this email as proof at entry points.</p>
<p>We will email you again once the payment is confirmed on the blockchain.</p>
<p>— Hope Foundation Conservation Team</p>"""
        send_email(data['email'], 'Your Conservation Fee Receipt (Pending)', email_html)
        return jsonify({
            'success': True,
            'message': 'Conservation fee recorded. Complete crypto transfer using the provided wallet address.',
            'transactionId': transaction_id,
            'receiptCode': receipt_code,
            'referenceCode': reference_code,
            'walletAddress': wallet_address,
            'status': 'pending',
            'confirmationEmail': data['email'],
            'emailMasked': mask_email(data['email']),
            'emailStatus': 'will-send-confirmation-after-blockchain',
            'supportedPaymentMethods': SUPPORTED_CRYPTO_METHODS
        })
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to create conservation fee.'}), 500

@app.route('/api/conservation/verify/<code>', methods=['GET'])
def verify_conservation_fee(code):
    fee = ConservationFee.query.filter_by(receipt_code=code).first()
    if not fee:
        return jsonify({'success': False, 'message': 'Receipt code not found.'}), 404
    return jsonify({'success': True, 'fee': fee.to_public_dict()})

# ------------------------------------------------------------------
# Conservation Fee Price List Endpoint
# ------------------------------------------------------------------
@app.route('/api/conservation/prices', methods=['GET'])
def get_conservation_price_list():
    """Return the structured conservation fee price list.
    This is static reference data; update the CONSERVATION_PRICE_LIST constant to change.
    """
    return jsonify({'success': True, 'prices': CONSERVATION_PRICE_LIST})

# ------------------------------------------------------------------
# User Donation Routes
# ------------------------------------------------------------------
@app.route('/api/user/donations', methods=['GET'])
@require_login
def get_user_donations():
    try:
        user = get_current_user()
        donations = Donation.query.filter_by(user_id=user.id).order_by(Donation.created_at.desc()).all()
        out = []
        for d in donations:
            out.append({
                'id': d.id,
                'amount': d.amount,
                'donation_type': d.donation_type,
                'payment_method': d.payment_method,
                'project': d.project,
                'status': d.status,
                'transaction_id': d.transaction_id,
                'created_at': d.created_at.isoformat(),
                'anonymous': d.anonymous
            })
        return jsonify({'success': True, 'donations': out})
    except Exception:
        return jsonify({'success': False, 'message': 'Failed to fetch donations'}), 500

@app.route('/api/user/dashboard', methods=['GET'])
@require_login
def user_dashboard():
    try:
        user = get_current_user()
        total_donations = db.session.query(db.func.sum(Donation.amount)).filter_by(user_id=user.id).scalar() or 0
        donation_count = Donation.query.filter_by(user_id=user.id).count()
        recent = Donation.query.filter_by(user_id=user.id).order_by(Donation.created_at.desc()).limit(5).all()
        return jsonify({'success': True, 'dashboard': {
            'user': user.to_dict(),
            'stats': {
                'total_donated': float(total_donations),
                'donation_count': donation_count,
                'last_donation': recent[0].created_at.isoformat() if recent else None
            },
            'recent_donations': [
                {'amount': d.amount, 'project': d.project, 'date': d.created_at.isoformat(), 'status': d.status}
                for d in recent
            ]
        }})
    except Exception:
        return jsonify({'success': False, 'message': 'Failed to fetch dashboard data'}), 500

# ------------------------------------------------------------------
# Newsletter
# ------------------------------------------------------------------
@app.route('/api/newsletter', methods=['POST'])
def newsletter_form():
    try:
        data = request.get_json() or {}
        if not data.get('email') or not validate_email_address(data['email']):
            return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        if Newsletter.query.filter_by(email=data['email']).first():
            return jsonify({'success': True, 'message': 'You are already subscribed to our newsletter!'})
        db.session.add(Newsletter(email=data['email']))
        db.session.commit()
        email_template = """
        <h2>Welcome to Hope Foundation Newsletter!</h2>
        <p>Thank you for subscribing to our newsletter.</p>
        <p>You will receive regular updates about our projects, impact stories, and ways to get involved.</p>
        <p>Best regards,<br>Hope Foundation Team</p>
        """
        send_email(data['email'], 'Welcome to Hope Foundation Newsletter', email_template)
        return jsonify({'success': True, 'message': 'Thank you for subscribing to our newsletter!'})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'}), 500

# ------------------------------------------------------------------
# Admin / Financial Overview
# ------------------------------------------------------------------
@app.route('/api/admin/stats')
def admin_stats():
    try:
        stats = {
            'contacts': Contact.query.count(),
            'donations': Donation.query.count(),
            'total_donations': db.session.query(db.func.sum(Donation.amount)).scalar() or 0,
            'newsletter_subscribers': Newsletter.query.count(),
            'registered_users': User.query.count(),
            'payments': Payment.query.count(),
            'recent_users': [u.to_dict() for u in User.query.order_by(User.created_at.desc()).limit(5).all()]
        }
        return jsonify(stats)
    except Exception:
        return jsonify({'error': 'Failed to fetch stats'}), 500

@app.route('/api/financial/overview')
def financial_overview():
    try:
        current_year = datetime.now().year
        year_donations = db.session.query(db.func.sum(Donation.amount)).filter(db.extract('year', Donation.created_at)==current_year).scalar() or 0
        year_expenses = db.session.query(db.func.sum(Expense.amount)).filter(db.extract('year', Expense.date)==current_year, Expense.status=='approved').scalar() or 0
        expense_breakdown_rows = db.session.query(Expense.category, db.func.sum(Expense.amount).label('total')).filter(db.extract('year', Expense.date)==current_year, Expense.status=='approved').group_by(Expense.category).all()
        breakdown = {row[0]: row[1] for row in expense_breakdown_rows}
        active_campaigns = Campaign.query.filter_by(status='active').all()
        campaign_data = []
        for c in active_campaigns:
            progress = (c.raised_amount / c.goal_amount * 100) if c.goal_amount > 0 else 0
            campaign_data.append({'id': c.id,'name': c.name,'goal': c.goal_amount,'raised': c.raised_amount,'progress': round(progress,1)})
        def pct(cat):
            return round((breakdown.get(cat,0) / year_expenses * 100),1) if year_expenses>0 else 0
        return jsonify({
            'year': current_year,
            'total_donations': year_donations,
            'total_expenses': year_expenses,
            'net_result': year_donations - year_expenses,
            'expense_breakdown': breakdown,
            'active_campaigns': campaign_data,
            'expense_ratio': {
                'program': pct('program'),
                'admin': pct('admin'),
                'fundraising': pct('fundraising')
            }
        })
    except Exception:
        return jsonify({'error': 'Failed to fetch financial overview'}), 500

@app.route('/api/financial/campaigns')
def get_campaigns():
    try:
        campaigns = Campaign.query.filter_by(status='active').all()
        out = []
        for c in campaigns:
            progress = (c.raised_amount / c.goal_amount * 100) if c.goal_amount > 0 else 0
            out.append({
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'goal_amount': c.goal_amount,
                'raised_amount': c.raised_amount,
                'progress': round(progress,1),
                'project_category': c.project_category,
                'start_date': c.start_date.isoformat() if c.start_date else None,
                'end_date': c.end_date.isoformat() if c.end_date else None
            })
        return jsonify(out)
    except Exception:
        return jsonify({'error': 'Failed to fetch campaigns'}), 500

@app.route('/api/financial/impact-calculator', methods=['POST'])
def impact_calculator():
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', 0))
        impact = {
            'clean_water_families': int(amount / 25),
            'school_meals': int(amount / 0.50),
            'medical_treatments': int(amount / 15),
            'educational_supplies': int(amount / 10),
            'emergency_kits': int(amount / 40)
        }
        return jsonify({'donation_amount': amount, 'impact': impact, 'message': f'Your ${amount} donation can make a significant impact!'})
    except Exception:
        return jsonify({'error': 'Failed to calculate impact'}), 500

@app.route('/api/financial/transparency')
def financial_transparency():
    try:
        current_year = datetime.now().year
        total_donations = db.session.query(db.func.sum(Donation.amount)).filter(db.extract('year', Donation.created_at)==current_year).scalar() or 0
        total_expenses = db.session.query(db.func.sum(Expense.amount)).filter(db.extract('year', Expense.date)==current_year, Expense.status=='approved').scalar() or 0
        program_expenses = db.session.query(db.func.sum(Expense.amount)).filter(db.extract('year', Expense.date)==current_year, Expense.category=='program', Expense.status=='approved').scalar() or 0
        admin_expenses = db.session.query(db.func.sum(Expense.amount)).filter(db.extract('year', Expense.date)==current_year, Expense.category=='admin', Expense.status=='approved').scalar() or 0
        fundraising_expenses = db.session.query(db.func.sum(Expense.amount)).filter(db.extract('year', Expense.date)==current_year, Expense.category=='fundraising', Expense.status=='approved').scalar() or 0
        def safe_pct(part):
            return round((part / total_expenses * 100),1) if total_expenses>0 else 0
        efficiency_rating = 'Excellent' if safe_pct(program_expenses) > 80 else 'Good' if safe_pct(program_expenses) > 70 else 'Fair'
        return jsonify({
            'year': current_year,
            'total_income': total_donations,
            'total_expenses': total_expenses,
            'program_percentage': safe_pct(program_expenses),
            'admin_percentage': safe_pct(admin_expenses),
            'fundraising_percentage': safe_pct(fundraising_expenses),
            'efficiency_rating': efficiency_rating,
            'program_expenses': program_expenses,
            'admin_expenses': admin_expenses,
            'fundraising_expenses': fundraising_expenses
        })
    except Exception:
        return jsonify({'error': 'Failed to fetch transparency data'}), 500

# ------------------------------------------------------------------
# DB Init
# ------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)