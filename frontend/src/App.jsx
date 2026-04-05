import { useState, useCallback, useRef, useEffect } from "react";

const API = "http://localhost:8000";
const fmt = (n) => n == null ? "—" : new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(n);
const pct = (n) => n == null ? "—" : `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;

const SAMPLE_VALID = {framework:"finrep",period:"2024-Q4",metadata:{entity:"Demo Bank Plc",currency:"EUR"},templates:{"F 01.01":{r010c010:5200000,r020c010:12800000,r030c010:3400000,r060c010:8900000,r100c010:82500000,r230c010:1200000,r240c010:500000,r250c010:4500000,r260c010:7800000,r280c010:3200000,r300c010:1900000,r340c010:2600000,r370c010:500000,r380c010:135000000,r390c010:8500000,r400c010:5200000,r430c010:78000000,r500c010:900000,r510c010:300000,r520c010:-4500000,r540c010:2100000,r560c010:0,r570c010:6800000,r590c010:1200000,r600c010:98500000,r610c010:36500000,r620c010:135000000}}};
const SAMPLE_FAIL = {framework:"finrep",period:"2024-Q4",metadata:{entity:"Demo Bank Plc",currency:"EUR"},templates:{"F 01.01":{r010c010:5200000,r020c010:12800000,r030c010:3400000,r060c010:8900000,r100c010:82500000,r230c010:1200000,r240c010:500000,r250c010:4500000,r260c010:7800000,r280c010:3200000,r300c010:1900000,r340c010:2600000,r370c010:500000,r380c010:145000000,r390c010:8500000,r400c010:5200000,r430c010:78000000,r500c010:900000,r510c010:300000,r520c010:4500000,r540c010:2100000,r560c010:0,r570c010:6800000,r590c010:1200000,r600c010:98500000,r610c010:36500000,r620c010:135000000}}};

const Pill = ({ status }) => {
  const m = { pass:{bg:"#ddf4e4",c:"#14622e",l:"PASS"},fail:{bg:"#fde2e2",c:"#91201a",l:"FAIL"},warning:{bg:"#fef3cd",c:"#7a5c00",l:"WARN"},skipped:{bg:"#eee",c:"#666",l:"SKIP"}}[status]||{bg:"#eee",c:"#666",l:status};
  return <span style={{display:"inline-block",padding:"3px 10px",borderRadius:4,background:m.bg,color:m.c,fontSize:11,fontWeight:700,letterSpacing:"0.06em",fontFamily:"'IBM Plex Mono',monospace"}}>{m.l}</span>;
};
const SevBadge = ({ severity }) => {
  const c = {error:"#91201a",warning:"#7a5c00",info:"#555"}[severity]||"#555";
  return <span style={{fontSize:10,color:c,fontWeight:600,textTransform:"uppercase",letterSpacing:"0.08em"}}>{severity}</span>;
};
const Card = ({ children, style }) => <div style={{background:"#fff",borderRadius:12,border:"1px solid #e8e6e1",overflow:"hidden",...style}}>{children}</div>;
const CardHeader = ({ left, right }) => <div style={{padding:"16px 24px",borderBottom:"1px solid #e8e6e1",display:"flex",justifyContent:"space-between",alignItems:"center"}}><span style={{fontSize:14,fontWeight:600,color:"#1a1a1a"}}>{left}</span>{right&&<span style={{fontSize:12,color:"#8a8a86"}}>{right}</span>}</div>;

export default function App() {
  const [view, setView] = useState("home");
  const [report, setReport] = useState(null);
  const [rules, setRules] = useState([]);
  const [historyList, setHistory] = useState([]);
  const [variance, setVariance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedRule, setExpanded] = useState(null);
  const [apiOk, setApiOk] = useState(null);
  const [dragOver, setDrag] = useState(false);
  const [fileName, setFileName] = useState(null);
  const fileRef = useRef(null);

  useEffect(() => { fetch(`${API}/`).then(r=>{setApiOk(r.ok)}).catch(()=>setApiOk(false)); }, []);

  const loadRules = useCallback(async () => {
    try { const r = await fetch(`${API}/taxonomies/finrep/rules`); setRules(await r.json()); setView("rules"); } catch(e) { setError(e.message); }
  }, []);

  const loadHistory = useCallback(async () => {
    try { const r = await fetch(`${API}/history`); setHistory(await r.json()); setView("history"); } catch(e) { setError(e.message); }
  }, []);

  const loadVariance = useCallback(async (entity, current, previous) => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/variance/${encodeURIComponent(entity)}?current=${encodeURIComponent(current)}&previous=${encodeURIComponent(previous)}&threshold=5`);
      if(!r.ok){const e=await r.json();throw new Error(e.detail);}
      setVariance(await r.json()); setView("variance");
    } catch(e) { setError(e.message); } finally { setLoading(false); }
  }, []);

  const runValidation = useCallback(async (data) => {
    setLoading(true); setError(null); setReport(null);
    try {
      const r = await fetch(`${API}/validate/finrep`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
      if(!r.ok){const e=await r.json();throw new Error(e.detail);}
      setReport(await r.json()); setView("results");
    } catch(e){setError(e.message);} finally{setLoading(false);}
  }, []);

  const handleFile = useCallback(async (file) => {
    if(!file) return; setLoading(true); setError(null); setFileName(file.name);
    const isXl = file.name.endsWith(".xlsx")||file.name.endsWith(".xls");
    if(!isXl && !file.name.endsWith(".json")){setError("Upload .xlsx or .json files.");setLoading(false);return;}
    try {
      if(isXl){
        const fd=new FormData();fd.append("file",file);fd.append("period","unknown");
        const r=await fetch(`${API}/validate/finrep/upload`,{method:"POST",body:fd});
        if(!r.ok){const e=await r.json();throw new Error(e.detail);}
        setReport(await r.json());setView("results");
      } else {
        const d=JSON.parse(await file.text()); await runValidation(d);
      }
    } catch(e){setError("Failed: "+e.message);} finally{setLoading(false);}
  }, [runValidation]);

  const goHome = () => { setView("home"); setReport(null); setError(null); setExpanded(null); setFileName(null); setVariance(null); };

  return (
    <div style={{fontFamily:"'DM Sans',system-ui,sans-serif",background:"#fafaf8",minHeight:"100vh"}}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
        @keyframes slideUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
        @keyframes spin{to{transform:rotate(360deg)}}*{box-sizing:border-box}`}</style>

      {/* NAV */}
      <header style={{padding:"14px 32px",borderBottom:"1px solid #e8e6e1",display:"flex",alignItems:"center",justifyContent:"space-between",background:"#fff"}}>
        <div style={{display:"flex",alignItems:"center",gap:14,cursor:"pointer"}} onClick={goHome}>
          <div style={{width:32,height:32,borderRadius:8,background:"#1a1a1a",display:"flex",alignItems:"center",justifyContent:"center",color:"#fff",fontSize:14,fontWeight:700}}>R</div>
          <div>
            <h1 style={{margin:0,fontSize:17,fontWeight:600,color:"#1a1a1a",letterSpacing:"-0.02em"}}>Regtura</h1>
            <p style={{margin:0,fontSize:11,color:"#8a8a86"}}>Regulatory validation engine</p>
          </div>
        </div>
        <nav style={{display:"flex",alignItems:"center",gap:6}}>
          {[{l:"Validate",v:"home"},{l:"Rules",v:"rules",fn:loadRules},{l:"History",v:"history",fn:loadHistory}].map(n=>(
            <button key={n.v} onClick={n.fn||goHome} style={{
              padding:"6px 14px",borderRadius:6,border:"none",fontSize:12,fontWeight:500,cursor:"pointer",fontFamily:"inherit",
              background:view===n.v?"#1a1a1a":"transparent",color:view===n.v?"#fff":"#8a8a86",
            }}>{n.l}</button>
          ))}
          <div style={{width:1,height:16,background:"#e8e6e1",margin:"0 6px"}}/>
          <div style={{display:"flex",alignItems:"center",gap:5,fontSize:11,color:"#8a8a86"}}>
            <div style={{width:6,height:6,borderRadius:"50%",background:apiOk?"#22c55e":apiOk===false?"#ef4444":"#ccc"}}/>
            {apiOk?"Connected":"Offline"}
          </div>
        </nav>
      </header>

      <main style={{maxWidth:920,margin:"0 auto",padding:"28px 24px"}}>

        {/* ERROR */}
        {error&&<div style={{padding:"14px 20px",borderRadius:10,background:"#fde2e2",border:"1px solid #f5c1c1",fontSize:13,color:"#91201a",marginBottom:16,animation:"slideUp .3s"}}><strong>Error:</strong> {error}</div>}

        {/* LOADING */}
        {loading&&<div style={{textAlign:"center",padding:"80px 0",animation:"slideUp .3s"}}><div style={{width:36,height:36,borderRadius:"50%",border:"3px solid #e8e6e1",borderTopColor:"#1a1a1a",animation:"spin .8s linear infinite",margin:"0 auto 14px"}}/><p style={{fontSize:13,color:"#8a8a86"}}>{fileName?`Parsing ${fileName}...`:"Running validation..."}</p></div>}

        {/* HOME */}
        {view==="home"&&!loading&&(
          <div style={{animation:"slideUp .4s"}}>
            <div style={{textAlign:"center",marginBottom:36}}>
              <h2 style={{fontSize:24,fontWeight:600,color:"#1a1a1a",letterSpacing:"-0.03em",margin:"0 0 6px"}}>Validate a regulatory submission</h2>
              <p style={{fontSize:14,color:"#8a8a86",margin:0}}>Upload your FINREP Excel template or JSON file to run EBA validation rules.</p>
            </div>
            <div onClick={()=>fileRef.current?.click()} onDrop={(e)=>{e.preventDefault();setDrag(false);handleFile(e.dataTransfer.files?.[0]);}} onDragOver={(e)=>{e.preventDefault();setDrag(true);}} onDragLeave={()=>setDrag(false)}
              style={{border:`2px dashed ${dragOver?"#1a1a1a":"#d4d4d0"}`,borderRadius:12,padding:"44px 32px",textAlign:"center",cursor:"pointer",marginBottom:14,background:dragOver?"#f5f5f0":"#fff",transition:"all .2s"}}
              onMouseOver={e=>{if(!dragOver)e.currentTarget.style.borderColor="#999"}} onMouseOut={e=>{if(!dragOver)e.currentTarget.style.borderColor="#d4d4d0"}}>
              <div style={{fontSize:28,marginBottom:10,color:"#d4d4d0"}}>+</div>
              <p style={{fontSize:14,fontWeight:500,color:"#1a1a1a",margin:"0 0 4px"}}>Upload Excel (.xlsx) or JSON file</p>
              <p style={{fontSize:12,color:"#8a8a86",margin:0}}>Drag and drop or click to browse</p>
              <input ref={fileRef} type="file" accept=".xlsx,.xls,.json" onChange={e=>handleFile(e.target.files?.[0])} style={{display:"none"}}/>
            </div>
            <div style={{display:"flex",gap:10,marginBottom:20}}>
              {[[SAMPLE_VALID,"Clean submission","All rules pass","#14622e"],[SAMPLE_FAIL,"With errors","Deliberate validation failures","#91201a"]].map(([d,t,s,c])=>(
                <button key={t} onClick={()=>runValidation(d)} style={{flex:1,padding:"14px 18px",borderRadius:10,border:"1px solid #e8e6e1",background:"#fff",cursor:"pointer",textAlign:"left",fontFamily:"inherit",transition:"border-color .2s"}}
                  onMouseOver={e=>e.currentTarget.style.borderColor=c} onMouseOut={e=>e.currentTarget.style.borderColor="#e8e6e1"}>
                  <div style={{fontSize:13,fontWeight:600,color:c,marginBottom:3}}>Sample — {t}</div>
                  <div style={{fontSize:12,color:"#8a8a86"}}>{s}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* RESULTS */}
        {view==="results"&&report&&!loading&&(
          <div style={{animation:"slideUp .4s"}}>
            {/* Report Header Card */}
            <Card style={{marginBottom:20}}>
              <div style={{padding:"24px 28px"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:20}}>
                  <div>
                    <div style={{fontSize:11,color:"#8a8a86",textTransform:"uppercase",letterSpacing:"0.1em",marginBottom:6}}>Validation report</div>
                    <h2 style={{margin:"0 0 4px",fontSize:22,fontWeight:700,color:"#1a1a1a",letterSpacing:"-0.02em"}}>{report.entity||"Unknown Entity"}</h2>
                    <div style={{display:"flex",gap:20,fontSize:13,color:"#555",marginTop:8,flexWrap:"wrap"}}>
                      <div><span style={{color:"#8a8a86"}}>Framework:</span> <strong style={{fontWeight:600}}>{report.framework_name||report.framework.toUpperCase()}</strong></div>
                      <div><span style={{color:"#8a8a86"}}>Period:</span> <strong style={{fontWeight:600}}>{report.period}</strong></div>
                      <div><span style={{color:"#8a8a86"}}>Currency:</span> <strong style={{fontWeight:600}}>{report.currency||"EUR"}</strong></div>
                      {report.templates_found?.length>0&&<div><span style={{color:"#8a8a86"}}>Templates:</span> <strong style={{fontWeight:600}}>{report.templates_found.join(", ")}</strong></div>}
                    </div>
                  </div>
                  <div style={{padding:"8px 18px",borderRadius:20,fontSize:13,fontWeight:600,background:report.passed?"#ddf4e4":"#fde2e2",color:report.passed?"#14622e":"#91201a",flexShrink:0}}>
                    {report.passed?"All checks passed":"Failures detected"}
                  </div>
                </div>
                <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
                  {[["Passed",report.summary.pass,"#ddf4e4","#14622e"],["Failed",report.summary.fail,"#fde2e2","#91201a"],["Warnings",report.summary.warning,"#fef3cd","#7a5c00"],["Skipped",report.summary.skipped,"#f1f1ef","#8a8a86"]].map(([l,n,bg,c])=>(
                    <div key={l} style={{padding:"12px 14px",borderRadius:8,background:bg}}>
                      <div style={{fontSize:24,fontWeight:700,color:c,fontFamily:"'IBM Plex Mono',monospace"}}>{n}</div>
                      <div style={{fontSize:11,color:c,opacity:.7,fontWeight:500}}>{l}</div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>

            {/* Results */}
            <Card>
              <CardHeader left="Validation results" right={`${report.results.length} rules executed`}/>
              {report.results.map((r,i) => {
                const open = expandedRule===i;
                const failed = r.status==="fail";
                return (
                  <div key={i} onClick={()=>setExpanded(open?null:i)} style={{padding:"14px 24px",borderBottom:i<report.results.length-1?"1px solid #f1f1ef":"none",cursor:"pointer",background:open?"#fafaf8":"#fff",transition:"background .15s"}}
                    onMouseOver={e=>{if(!open)e.currentTarget.style.background="#fafaf8"}} onMouseOut={e=>{if(!open)e.currentTarget.style.background="#fff"}}>
                    <div style={{display:"flex",alignItems:"center",gap:12}}>
                      <Pill status={r.status}/>
                      <div style={{flex:1,minWidth:0}}>
                        <div style={{fontSize:13,fontWeight:600,color:"#1a1a1a"}}>{r.rule_name}</div>
                        <div style={{fontSize:12,color:"#8a8a86",marginTop:1}}>{r.rule_id} · <SevBadge severity={r.severity}/></div>
                      </div>
                      <span style={{fontSize:14,color:"#d4d4d0",transition:"transform .2s",transform:open?"rotate(90deg)":"rotate(0)"}}>▸</span>
                    </div>
                    {open&&(
                      <div style={{marginTop:14,animation:"slideUp .2s"}}>
                        <div style={{padding:"14px 18px",background:failed?"#fef8f8":"#f8fdf8",borderRadius:8,border:`1px solid ${failed?"#f5d5d5":"#d5efd5"}`,marginBottom:12}}>
                          <div style={{fontSize:13,color:failed?"#91201a":"#14622e",lineHeight:1.7,fontWeight:500}}>{r.detail}</div>
                        </div>
                        {(r.expected!=null||r.actual!=null)&&(
                          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10,marginBottom:12}}>
                            {r.expected!=null&&<div style={{padding:"10px 14px",background:"#fafaf8",borderRadius:6}}><div style={{fontSize:11,color:"#8a8a86",marginBottom:2}}>Expected</div><div style={{fontSize:14,fontWeight:600,fontFamily:"'IBM Plex Mono',monospace"}}>{fmt(r.expected)}</div></div>}
                            {r.actual!=null&&<div style={{padding:"10px 14px",background:"#fafaf8",borderRadius:6}}><div style={{fontSize:11,color:"#8a8a86",marginBottom:2}}>Actual</div><div style={{fontSize:14,fontWeight:600,fontFamily:"'IBM Plex Mono',monospace"}}>{fmt(r.actual)}</div></div>}
                            {r.delta!=null&&<div style={{padding:"10px 14px",background:r.delta!==0?"#fde2e2":"#ddf4e4",borderRadius:6}}><div style={{fontSize:11,color:"#8a8a86",marginBottom:2}}>Delta</div><div style={{fontSize:14,fontWeight:600,fontFamily:"'IBM Plex Mono',monospace",color:r.delta!==0?"#91201a":"#14622e"}}>{r.delta>0?"+":""}{fmt(r.delta)}</div></div>}
                          </div>
                        )}
                        {(r.what||r.why||r.fix)&&(
                          <div style={{display:"grid",gap:8}}>
                            {r.what&&<div style={{padding:"10px 14px",background:"#f5f5f0",borderRadius:6}}><div style={{fontSize:11,color:"#8a8a86",marginBottom:2,fontWeight:600}}>What this checks</div><div style={{fontSize:12,color:"#555",lineHeight:1.6}}>{r.what}</div></div>}
                            {failed&&r.why&&<div style={{padding:"10px 14px",background:"#fef8f0",borderRadius:6}}><div style={{fontSize:11,color:"#8a6a00",marginBottom:2,fontWeight:600}}>Why this might happen</div><div style={{fontSize:12,color:"#555",lineHeight:1.6}}>{r.why}</div></div>}
                            {failed&&r.fix&&<div style={{padding:"10px 14px",background:"#f0f8f0",borderRadius:6}}><div style={{fontSize:11,color:"#14622e",marginBottom:2,fontWeight:600}}>How to fix it</div><div style={{fontSize:12,color:"#555",lineHeight:1.6}}>{r.fix}</div></div>}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </Card>
          </div>
        )}

        {/* RULES BROWSER */}
        {view==="rules"&&!loading&&(
          <div style={{animation:"slideUp .4s"}}>
            <h2 style={{fontSize:20,fontWeight:600,color:"#1a1a1a",margin:"0 0 6px"}}>FINREP validation rules</h2>
            <p style={{fontSize:13,color:"#8a8a86",margin:"0 0 20px"}}>All EBA validation rules currently implemented in Regtura.</p>
            <Card>
              {rules.map((r,i)=>(
                <div key={i} onClick={()=>setExpanded(expandedRule===i?null:i)} style={{padding:"16px 24px",borderBottom:i<rules.length-1?"1px solid #f1f1ef":"none",cursor:"pointer",transition:"background .15s"}}
                  onMouseOver={e=>e.currentTarget.style.background="#fafaf8"} onMouseOut={e=>e.currentTarget.style.background="#fff"}>
                  <div style={{display:"flex",alignItems:"center",gap:12}}>
                    <code style={{fontSize:12,color:"#8a8a86",fontFamily:"'IBM Plex Mono',monospace",minWidth:70}}>{r.rule_id}</code>
                    <div style={{flex:1}}>
                      <div style={{fontSize:14,fontWeight:600,color:"#1a1a1a"}}>{r.name}</div>
                      <div style={{fontSize:12,color:"#8a8a86",marginTop:1}}>{r.template} · <SevBadge severity={r.severity}/> · {r.rule_type}</div>
                    </div>
                    <span style={{fontSize:14,color:"#d4d4d0",transition:"transform .2s",transform:expandedRule===i?"rotate(90deg)":"rotate(0)"}}>▸</span>
                  </div>
                  {expandedRule===i&&(
                    <div style={{marginTop:12,display:"grid",gap:8,animation:"slideUp .2s"}}>
                      <div style={{padding:"10px 14px",background:"#f5f5f0",borderRadius:6}}><div style={{fontSize:11,color:"#8a8a86",fontWeight:600,marginBottom:2}}>What this checks</div><div style={{fontSize:12,color:"#555",lineHeight:1.6}}>{r.what}</div></div>
                      <div style={{padding:"10px 14px",background:"#fef8f0",borderRadius:6}}><div style={{fontSize:11,color:"#8a6a00",fontWeight:600,marginBottom:2}}>Why it matters</div><div style={{fontSize:12,color:"#555",lineHeight:1.6}}>{r.why}</div></div>
                      <div style={{padding:"10px 14px",background:"#f0f8f0",borderRadius:6}}><div style={{fontSize:11,color:"#14622e",fontWeight:600,marginBottom:2}}>How to fix a failure</div><div style={{fontSize:12,color:"#555",lineHeight:1.6}}>{r.fix}</div></div>
                      <div style={{padding:"10px 14px",background:"#fafaf8",borderRadius:6}}><div style={{fontSize:11,color:"#8a8a86",fontWeight:600,marginBottom:2}}>Formula</div><code style={{fontSize:12,color:"#555",fontFamily:"'IBM Plex Mono',monospace"}}>{r.formula}</code></div>
                    </div>
                  )}
                </div>
              ))}
            </Card>
          </div>
        )}

        {/* HISTORY */}
        {view==="history"&&!loading&&(
          <div style={{animation:"slideUp .4s"}}>
            <h2 style={{fontSize:20,fontWeight:600,color:"#1a1a1a",margin:"0 0 6px"}}>Submission history</h2>
            <p style={{fontSize:13,color:"#8a8a86",margin:"0 0 20px"}}>Previously validated submissions. Select two periods to compare.</p>
            {historyList.length===0?(
              <Card style={{padding:"40px",textAlign:"center"}}><p style={{color:"#8a8a86",fontSize:14}}>No submissions yet. Validate a file to see it here.</p></Card>
            ):(
              <Card>
                <CardHeader left="Submissions" right={`${historyList.length} records`}/>
                {historyList.map((s,i)=>(
                  <div key={i} style={{padding:"14px 24px",borderBottom:i<historyList.length-1?"1px solid #f1f1ef":"none",display:"flex",alignItems:"center",gap:16}}>
                    <div style={{width:8,height:8,borderRadius:"50%",background:s.passed?"#22c55e":"#ef4444",flexShrink:0}}/>
                    <div style={{flex:1}}>
                      <div style={{fontSize:14,fontWeight:600,color:"#1a1a1a"}}>{s.entity}</div>
                      <div style={{fontSize:12,color:"#8a8a86",marginTop:2}}>
                        {s.framework.toUpperCase()} · {s.period} · {s.filename||"JSON upload"} · {new Date(s.uploaded_at).toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"})}
                      </div>
                    </div>
                    <div style={{fontSize:12,color:"#8a8a86"}}>{s.summary.pass} pass / {s.summary.fail} fail</div>
                  </div>
                ))}
                {/* Variance launcher */}
                {(()=>{
                  const entities = [...new Set(historyList.map(h=>h.entity))];
                  const byEntity = {};
                  historyList.forEach(h=>{if(!byEntity[h.entity])byEntity[h.entity]=[];byEntity[h.entity].push(h.period);});
                  const pairs = entities.filter(e=>byEntity[e].length>=2);
                  if(!pairs.length) return null;
                  return (
                    <div style={{padding:"16px 24px",borderTop:"1px solid #e8e6e1",background:"#fafaf8"}}>
                      <div style={{fontSize:13,fontWeight:600,color:"#1a1a1a",marginBottom:8}}>Variance analysis</div>
                      <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
                        {pairs.map(e=>{
                          const periods = byEntity[e].sort().reverse();
                          return (
                            <button key={e} onClick={()=>loadVariance(e,periods[0],periods[1])} style={{
                              padding:"8px 16px",borderRadius:6,border:"1px solid #e8e6e1",background:"#fff",cursor:"pointer",fontFamily:"inherit",fontSize:12,
                            }} onMouseOver={e=>e.currentTarget.style.borderColor="#1a1a1a"} onMouseOut={e=>e.currentTarget.style.borderColor="#e8e6e1"}>
                              {e}: {periods[1]} → {periods[0]}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })()}
              </Card>
            )}
          </div>
        )}

        {/* VARIANCE */}
        {view==="variance"&&variance&&!loading&&(
          <div style={{animation:"slideUp .4s"}}>
            <Card style={{marginBottom:20}}>
              <div style={{padding:"24px 28px"}}>
                <div style={{fontSize:11,color:"#8a8a86",textTransform:"uppercase",letterSpacing:"0.1em",marginBottom:6}}>Variance analysis</div>
                <h2 style={{margin:"0 0 4px",fontSize:20,fontWeight:700,color:"#1a1a1a"}}>{variance.entity}</h2>
                <div style={{fontSize:13,color:"#555"}}>{variance.previous_period} → {variance.current_period} · {variance.template}</div>
              </div>
            </Card>

            {variance.material_changes.length>0&&(
              <Card style={{marginBottom:20}}>
                <CardHeader left={`Material changes (≥5%)`} right={`${variance.material_changes.length} items`}/>
                {variance.material_changes.map((v,i)=>(
                  <div key={i} style={{padding:"12px 24px",borderBottom:i<variance.material_changes.length-1?"1px solid #f1f1ef":"none",display:"flex",alignItems:"center",gap:14}}>
                    <div style={{width:6,height:6,borderRadius:"50%",background:v.direction==="increase"?"#22c55e":"#ef4444",flexShrink:0}}/>
                    <div style={{flex:1,fontSize:13,color:"#1a1a1a",fontWeight:500}}>{v.label}</div>
                    <div style={{fontSize:12,color:"#8a8a86",fontFamily:"'IBM Plex Mono',monospace"}}>{fmt(v.previous_value)} → {fmt(v.current_value)}</div>
                    <div style={{fontSize:13,fontWeight:600,fontFamily:"'IBM Plex Mono',monospace",color:v.direction==="increase"?"#14622e":"#91201a",minWidth:60,textAlign:"right"}}>{pct(v.percentage_change)}</div>
                  </div>
                ))}
              </Card>
            )}

            <Card>
              <CardHeader left="All line items" right={`${variance.items.length} cells compared`}/>
              <div style={{maxHeight:500,overflowY:"auto"}}>
                {variance.items.map((v,i)=>(
                  <div key={i} style={{padding:"10px 24px",borderBottom:i<variance.items.length-1?"1px solid #f5f5f0":"none",display:"flex",alignItems:"center",gap:12,fontSize:12}}>
                    <code style={{color:"#b4b4b0",fontFamily:"'IBM Plex Mono',monospace",minWidth:64,fontSize:11}}>{v.cell_ref}</code>
                    <div style={{flex:1,color:"#555"}}>{v.label}</div>
                    <div style={{color:"#8a8a86",fontFamily:"'IBM Plex Mono',monospace",minWidth:90,textAlign:"right"}}>{fmt(v.previous_value)}</div>
                    <div style={{color:"#8a8a86"}}>→</div>
                    <div style={{color:"#1a1a1a",fontFamily:"'IBM Plex Mono',monospace",minWidth:90,textAlign:"right",fontWeight:500}}>{fmt(v.current_value)}</div>
                    <div style={{fontFamily:"'IBM Plex Mono',monospace",minWidth:60,textAlign:"right",fontWeight:600,
                      color:v.percentage_change==null?"#ccc":Math.abs(v.percentage_change)>=10?"#91201a":Math.abs(v.percentage_change)>=5?"#7a5c00":"#14622e"
                    }}>{pct(v.percentage_change)}</div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}
      </main>

      <footer style={{padding:"20px 32px",textAlign:"center",fontSize:12,color:"#c4c4c0",borderTop:"1px solid #e8e6e1",marginTop:40}}>
        Regtura v0.1.0 — Open source regulatory reporting suite
      </footer>
    </div>
  );
}