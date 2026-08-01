"""Clean-slate wipe for tutorial recording: drop MNB-HR + non-spadmin identities."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from . import IIQ_DOCKER_CONTAINER, ROOT

WIPE_RULE = """<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Rule PUBLIC "sailpoint.dtd" "sailpoint.dtd">
<Rule language="beanshell" name="MNB-Rule-TutorialWipe04">
  <Description>Tutorial preflight: wipe MNB-HR related objects and non-spadmin identities.</Description>
  <Source><![CDATA[
      import sailpoint.api.Terminator;
      import sailpoint.object.Application;
      import sailpoint.object.Identity;
      import sailpoint.object.QueryOptions;
      import sailpoint.object.TaskDefinition;
      import sailpoint.tools.Util;
      import java.util.ArrayList;
      import java.util.Iterator;
      import java.util.List;

      Terminator terminator = new Terminator(context);
      StringBuilder log = new StringBuilder();

      QueryOptions qo = new QueryOptions();
      Iterator it = context.search(Identity.class, qo);
      List toKill = new ArrayList();
      while (it.hasNext()) {
        Identity id = (Identity) it.next();
        if (id != null && !"spadmin".equals(id.getName())) {
          toKill.add(id.getName());
        }
      }
      Util.flushIterator(it);
      int n = 0;
      for (Object name : toKill) {
        Identity id = context.getObjectByName(Identity.class, (String) name);
        if (id != null) {
          terminator.deleteObject(id);
          n++;
        }
      }
      log.append("identities=").append(n).append(" ");

      String[] apps = {"MNB-HR"};
      for (int i = 0; i < apps.length; i++) {
        Application a = context.getObjectByName(Application.class, apps[i]);
        if (a != null) {
          terminator.deleteObject(a);
          log.append("delApp=").append(apps[i]).append(" ");
        }
      }

      String[] tasks = {"Aggregate MNB-HR", "Aggregate MNB-HR-DRYRUN"};
      for (int i = 0; i < tasks.length; i++) {
        TaskDefinition t = context.getObjectByName(TaskDefinition.class, tasks[i]);
        if (t != null) {
          terminator.deleteObject(t);
          log.append("delTask=").append(tasks[i]).append(" ");
        }
      }

      context.commitTransaction();
      return "OK " + log.toString();
  ]]></Source>
</Rule>
"""


def wipe_lesson04(container: str | None = None) -> str:
    """Import and run wipe rule inside the IIQ container. Returns console output."""
    cname = container or IIQ_DOCKER_CONTAINER
    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / "MNB-Rule-TutorialWipe04.xml"
        local.write_text(WIPE_RULE, encoding="utf-8")
        subprocess.run(
            ["docker", "cp", str(local), f"{cname}:/tmp/MNB-Rule-TutorialWipe04.xml"],
            check=True,
        )
    proc = subprocess.run(
        [
            "docker",
            "exec",
            cname,
            "sh",
            "-c",
            "cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin && "
            "./iiq console iiqBeans <<'EOF'\n"
            "import /tmp/MNB-Rule-TutorialWipe04.xml\n"
            "rule MNB-Rule-TutorialWipe04\n"
            "EOF",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise SystemExit(f"wipe failed (exit {proc.returncode}):\n{out[-2000:]}")
    return out
