r"""run_checks - the gdsstats runner.

    python run_checks.py {validate <name> | validate-all | suite}

Writes fixed-path _checks/result.json + last.log before printing (dropped-launch recovery)."""
import sys, os, json, time, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CHK = os.path.join(HERE, "_checks")
os.makedirs(CHK, exist_ok=True)
PY = sys.executable
MODULES = ["load", "counts", "hierarchy", "extremes", "report", "cli"]


def _write(result, log):
    result["ts"] = time.time()
    with open(os.path.join(CHK, "last.log"), "w", encoding="utf-8") as f:
        f.write(log)
    with open(os.path.join(CHK, "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


def _run(cmd):
    p = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def validate(name):
    path = os.path.join(HERE, f"{name}.py")
    if not os.path.exists(path):
        _write({"mode": "validate", "name": name, "status": "FAIL", "reason": "no module"}, "")
        print(f"no module {name}.py"); return 1
    t0 = time.time()
    rc, out = _run([PY, path, "--validate"])
    ok = rc == 0 and "RESULT: PASS" in out and "FAIL" not in out.split("RESULT:")[-1]
    status = "PASS" if ok else "FAIL"
    _write({"mode": "validate", "name": name, "status": status, "dur": round(time.time() - t0, 1)}, out)
    print(out.rstrip())
    print(f"CHECKS_DONE status={status} mode=validate name={name} dur={time.time()-t0:.1f}s")
    return 0 if ok else 1


def validate_all():
    t0 = time.time(); results, log = {}, ""
    for name in MODULES:
        if not os.path.exists(os.path.join(HERE, f"{name}.py")):
            continue
        rc, out = _run([PY, os.path.join(HERE, f"{name}.py"), "--validate"])
        ok = rc == 0 and "RESULT: PASS" in out and "FAIL" not in out.split("RESULT:")[-1]
        results[name] = "PASS" if ok else "FAIL"
        log += f"===== {name} =====\n{out}\n"
    npass = sum(v == "PASS" for v in results.values())
    status = "PASS" if npass == len(results) and results else "FAIL"
    _write({"mode": "validate-all", "status": status, "passed": npass, "total": len(results),
            "per_module": results, "dur": round(time.time() - t0, 1)}, log)
    print(log.rstrip())
    print(f"CHECKS_DONE status={status} mode=validate-all passed={npass}/{len(results)}")
    return 0 if status == "PASS" else 1


def suite():
    t0 = time.time()
    rc, out = _run([PY, "-m", "pytest", "-q", os.path.join(HERE, "tests")])
    last = out.strip().splitlines()[-1] if out.strip() else ""
    status = "PASS" if rc == 0 else "FAIL"
    _write({"mode": "suite", "status": status, "summary": last, "dur": round(time.time() - t0, 1)}, out)
    print(out.rstrip())
    print(f"CHECKS_DONE status={status} mode=suite dur={time.time()-t0:.1f}s")
    return 0 if rc == 0 else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    mode = sys.argv[1]
    if mode in ("validate", "tool") and len(sys.argv) > 2:
        return validate(sys.argv[2])
    if mode == "validate-all":
        return validate_all()
    if mode == "suite":
        return suite()
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main())
