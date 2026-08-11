"use client";

import { FormEvent, useMemo, useState } from "react";

type Ref = { evidence_id: string; label: string; page?: number | null; excerpt?: string | null };
type Hypothesis = { title: string; root_cause: string; confidence: number; supporting_evidence: Ref[]; unresolved_uncertainty: string[] };
type DiagnosticTest = { name: string; procedure: string[]; expected_observation: string; interpretation: string; safety_notes: string[] };
type Trace = { agent: string; status: string; duration_ms: number; note?: string | null };
type Report = {
  case_id: string;
  summary: string;
  diagnosis: { primary?: Hypothesis | null; alternatives: Hypothesis[]; tests: DiagnosticTest[]; proposed_fix: string[]; safety_considerations: string[] };
  verification: { accepted: boolean; confidence_adjustment: number; challenges: string[]; missing_evidence: string[] };
  evidence_used: Ref[];
  agent_trace: Trace[];
  unresolved_uncertainty: string[];
  disclaimer: string;
};

const API = process.env.NEXT_PUBLIC_BENCHMIND_API ?? "http://localhost:8000";

function pct(value: number) {
  return `${Math.round(value * 100)}%`;
}

export default function Home() {
  const [question, setQuestion] = useState("My HC-SR04 always reads 0 cm. What is the most likely fault?");
  const [files, setFiles] = useState<File[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const adjustedConfidence = useMemo(() => {
    if (!report?.diagnosis.primary) return null;
    return Math.max(0, Math.min(1, report.diagnosis.primary.confidence + report.verification.confidence_adjustment));
  }, [report]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setReport(null);
    const form = new FormData();
    form.append("question", question);
    files.forEach((file) => form.append("files", file));
    try {
      const response = await fetch(`${API}/api/v1/analyze`, { method: "POST", body: form });
      if (!response.ok) throw new Error((await response.json()).detail ?? `HTTP ${response.status}`);
      setReport(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  }

  async function runDemo() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`${API}/api/v1/demo/esp32_wrong_gpio`, { method: "POST" });
      if (!response.ok) throw new Error("Demo request failed");
      setReport(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand"><span className="mark">BM</span><div><strong>BenchMind AI</strong><small>Engineering Diagnostic Workspace</small></div></div>
        <div className="status"><span /> Evidence-grounded V1</div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">MULTIMODAL · MULTI-AGENT · VERIFICATION-FIRST</p>
          <h1>Debug engineering systems from evidence, not guesses.</h1>
          <p className="lede">Upload firmware, logs, PDFs, telemetry, schematics, or hardware images. BenchMind routes only the needed specialists, challenges the diagnosis, and returns a traceable test plan.</p>
        </div>
        <div className="heroStats">
          <div><strong>9</strong><span>agent roles</span></div>
          <div><strong>12</strong><span>files / case</span></div>
          <div><strong>0</strong><span>required paid APIs</span></div>
        </div>
      </section>

      <div className="workspace">
        <form className="panel inputPanel" onSubmit={submit}>
          <div className="panelTitle"><span>01</span><div><strong>Case input</strong><small>Question + engineering evidence</small></div></div>
          <label>Engineering question</label>
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={6} />
          <label className="dropzone">
            <input multiple type="file" onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
            <span className="uploadIcon">＋</span>
            <strong>Attach evidence</strong>
            <small>PDF · image · INO · C/C++ · Python · logs · CSV · config</small>
          </label>
          {files.length > 0 && <div className="fileList">{files.map((file) => <span key={file.name}>{file.name}</span>)}</div>}
          <button className="primary" disabled={busy}>{busy ? "Analyzing…" : "Analyze case"}</button>
          <button className="secondary" type="button" onClick={runDemo} disabled={busy}>Run built-in ESP32 demo</button>
          {error && <div className="error">{error}</div>}
        </form>

        <section className="panel resultPanel">
          <div className="panelTitle"><span>02</span><div><strong>Diagnosis</strong><small>Evidence-backed output</small></div></div>
          {!report && <div className="empty"><div className="scope" /><strong>No case analyzed yet</strong><p>Your diagnosis, confidence, verifier challenges, and test plan will appear here.</p></div>}
          {report && <>
            <div className={`verdict ${report.verification.accepted ? "accepted" : "uncertain"}`}>
              <div><small>PRIMARY HYPOTHESIS</small><h2>{report.diagnosis.primary?.title ?? "Insufficient evidence"}</h2></div>
              <div className="confidence"><strong>{adjustedConfidence === null ? "—" : pct(adjustedConfidence)}</strong><span>adjusted confidence</span></div>
            </div>
            <p className="rootCause">{report.diagnosis.primary?.root_cause ?? report.summary}</p>

            <div className="grid2">
              <div className="subcard"><h3>Verifier</h3><p className="verifierState">{report.verification.accepted ? "Supported after challenge" : "Not yet verified"}</p>{report.verification.challenges.map((item) => <p className="muted" key={item}>— {item}</p>)}</div>
              <div className="subcard"><h3>Proposed fix</h3>{report.diagnosis.proposed_fix.length ? report.diagnosis.proposed_fix.map((item) => <p key={item}>— {item}</p>) : <p className="muted">No fix is asserted without a supported root cause.</p>}</div>
            </div>

            <h3 className="sectionHead">Diagnostic test plan</h3>
            {report.diagnosis.tests.map((test) => <div className="testCard" key={test.name}><strong>{test.name}</strong><ol>{test.procedure.map((step) => <li key={step}>{step}</li>)}</ol><p><b>Expected:</b> {test.expected_observation}</p></div>)}

            <h3 className="sectionHead">Evidence used</h3>
            <div className="evidenceList">{report.evidence_used.length ? report.evidence_used.map((item, i) => <div key={`${item.evidence_id}-${i}`}><span>{String(i + 1).padStart(2, "0")}</span><div><strong>{item.label}{item.page ? ` · p.${item.page}` : ""}</strong>{item.excerpt && <small>{item.excerpt}</small>}</div></div>) : <p className="muted">No evidence citations were used.</p>}</div>
          </>}
        </section>

        <aside className="panel tracePanel">
          <div className="panelTitle"><span>03</span><div><strong>Agent trace</strong><small>Only invoked when useful</small></div></div>
          {!report ? <div className="agentPreview">{["Supervisor", "Firmware", "Datasheet", "Telemetry", "Diagnosis", "Verifier"].map((name) => <div key={name}><i />{name}<span>standby</span></div>)}</div> : <div className="timeline">{report.agent_trace.map((trace) => <div key={`${trace.agent}-${trace.duration_ms}`}><i className={trace.status} /><div><strong>{trace.agent.replaceAll("_", " ")}</strong><small>{trace.note ?? trace.status}</small></div><span>{trace.duration_ms.toFixed(1)} ms</span></div>)}</div>}
          <div className="boundary"><strong>Reliability boundary</strong><p>{report?.disclaimer ?? "BenchMind separates observations from hypotheses and refuses to force a diagnosis when evidence is insufficient."}</p></div>
        </aside>
      </div>
    </main>
  );
}
