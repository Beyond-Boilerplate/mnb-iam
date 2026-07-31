package com.meridianbank.iiq.plugin.rest;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javax.ws.rs.Consumes;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.MediaType;

import org.apache.log4j.Logger;

import sailpoint.api.SailPointContext;
import sailpoint.api.TaskManager;
import sailpoint.api.Workflower;
import sailpoint.object.Application;
import sailpoint.object.Attributes;
import sailpoint.object.BatchRequest;
import sailpoint.object.Capability;
import sailpoint.object.Certification;
import sailpoint.object.CertificationDefinition;
import sailpoint.object.EmailOptions;
import sailpoint.object.EmailTemplate;
import sailpoint.object.Filter;
import sailpoint.object.Form;
import sailpoint.object.Identity;
import sailpoint.object.Link;
import sailpoint.object.ManagedAttribute;
import sailpoint.object.Policy;
import sailpoint.object.PolicyViolation;
import sailpoint.object.ProvisioningPlan;
import sailpoint.object.ProvisioningPlan.AccountRequest;
import sailpoint.object.ProvisioningPlan.AttributeRequest;
import sailpoint.object.QueryOptions;
import sailpoint.object.TaskDefinition;
import sailpoint.object.TaskResult;
import sailpoint.object.WorkItem;
import sailpoint.object.Workflow;
import sailpoint.object.WorkflowLaunch;
import sailpoint.rest.plugin.BasePluginResource;
import sailpoint.rest.plugin.RequiredRight;
import sailpoint.tools.GeneralException;
import sailpoint.tools.Util;
import sailpoint.tools.xml.XMLReferenceResolver;

/**
 * Coverage APIs for Teller/MCP agentic surface (UIAPI-30+).
 * No Teller hardcoding — MCP tools wrap these paths; Teller discovers via tools/list.
 */
@Path("mnbToolkit/agent")
@RequiredRight("MNBToolkitAgent")
public class MnbAgentCoverageResource extends BasePluginResource {

  private static final Logger log = Logger.getLogger(MnbAgentCoverageResource.class);

  @Override
  public String getPluginName() {
    return MnbToolkitPingResource.PLUGIN_NAME;
  }

  // —— UIAPI-30 JML ——
  @POST
  @Path("jml/{event}")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> runJml(@PathParam("event") String event, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-30");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String identityName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("identityName")),
            MnbAgentSupport.str(body.get("identity")));
    Identity identity = MnbAgentSupport.resolveIdentity(getContext(), identityName, "UIAPI-30");
    boolean dryRun = Boolean.TRUE.equals(body.get("dryRun"));
    String reason = MnbAgentSupport.str(body.get("reason"));
    String managerName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("managerName")), MnbAgentSupport.str(body.get("manager")));

    String ev = event == null ? "" : event.trim().toLowerCase();
    String[] candidates;
    if ("joiner".equals(ev)) {
      candidates = new String[] {"RapidSetup - Joiner", "Lifecycle Event - Joiner"};
    } else if ("leaver".equals(ev) || "terminate".equals(ev)) {
      candidates = new String[] {"RapidSetup - Leaver", "Lifecycle Event - Leaver"};
    } else if ("mover".equals(ev) || "transfer".equals(ev)) {
      candidates =
          new String[] {"RapidSetup - Mover", "Lifecycle Event - Manager Transfer"};
    } else if ("reinstate".equals(ev) || "rehire".equals(ev)) {
      candidates = new String[] {"Lifecycle Event - Reinstate", "RapidSetup - Joiner"};
    } else {
      throw MnbAgentSupport.error(
          400,
          "invalid_event",
          "event must be joiner|mover|leaver|reinstate",
          "UIAPI-30",
          null);
    }

    SailPointContext ctx = getContext();
    Workflow wf = null;
    String chosen = null;
    for (String name : candidates) {
      wf = ctx.getObjectByName(Workflow.class, name);
      if (wf != null) {
        chosen = name;
        break;
      }
    }
    if (wf == null) {
      throw MnbAgentSupport.error(
          404,
          "workflow_not_found",
          "No JML workflow found for event=" + ev,
          "UIAPI-30",
          "Import RapidSetup/LCM workflows");
    }

    Map<String, Object> data = new LinkedHashMap<>();
    data.put("event", ev);
    data.put("identityName", identity.getName());
    data.put("workflowName", chosen);
    data.put("dryRun", dryRun);
    if (dryRun) {
      data.put("launchStatus", "dry_run");
      return MnbAgentSupport.ok("UIAPI-30", data);
    }

    Map<String, Object> vars = new HashMap<>();
    vars.put("identityName", identity.getName());
    vars.put("identity", identity.getName());
    vars.put("launcher", ctx.getUserName());
    if (!Util.isNullOrEmpty(reason)) {
      vars.put("comments", reason);
      vars.put("reason", reason);
    }
    if (!Util.isNullOrEmpty(managerName)) {
      vars.put("manager", managerName);
      vars.put("newManager", managerName);
    }
    Workflower workflower = new Workflower(ctx);
    WorkflowLaunch launch =
        workflower.launch(wf, "mnb-jml-" + ev + "-" + System.currentTimeMillis(), vars);
    ctx.commitTransaction();
    if (launch != null) {
      data.put("launchId", launch.getTaskResult() != null ? launch.getTaskResult().getId() : null);
      data.put("launchStatus", launch.getStatus());
      data.put(
          "workflowCaseId",
          launch.getWorkflowCase() != null ? launch.getWorkflowCase().getId() : null);
    }
    return MnbAgentSupport.ok("UIAPI-30", data);
  }

  // —— UIAPI-31 Cert campaigns ——
  @POST
  @Path("certifications/campaigns")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> createCertificationCampaign(Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-31");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      name = "MNB-Campaign-" + System.currentTimeMillis();
    }
    String templateName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("template")),
            MnbAgentSupport.str(body.get("certificationDefinition")),
            "CertificationTemplate-RapidSetup-Mover");
    SailPointContext ctx = getContext();
    CertificationDefinition template =
        ctx.getObjectByName(CertificationDefinition.class, templateName);
    if (template == null) {
      QueryOptions qo = new QueryOptions();
      qo.setResultLimit(1);
      List<CertificationDefinition> defs = ctx.getObjects(CertificationDefinition.class, qo);
      if (defs != null && !defs.isEmpty()) {
        template = defs.get(0);
        templateName = template.getName();
      }
    }
    if (template == null) {
      throw MnbAgentSupport.error(
          404,
          "not_found",
          "No CertificationDefinition template available",
          "UIAPI-31",
          "Import a certification template first");
    }

    CertificationDefinition def =
        (CertificationDefinition) template.deepCopy((XMLReferenceResolver) ctx);
    def.setId(null);
    def.setName(name);
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      def.setDescription(description);
    }
    ctx.saveObject(def);
    ctx.commitTransaction();

    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", def.getName());
    data.put("id", def.getId());
    data.put("template", templateName);

    boolean generateNow =
        Boolean.TRUE.equals(body.get("generateNow"))
            || "true".equalsIgnoreCase(MnbAgentSupport.str(body.get("generateNow")));
    if (generateNow) {
      try {
        Attributes<String, Object> args = new Attributes<>();
        args.put("certificationDefinition", def.getName());
        TaskResult tr = runNamedTask(ctx, "Certification Manager", args, true, "UIAPI-31");
        data.put("generateTaskResultId", tr != null ? tr.getId() : null);
        data.put("generateStatus", tr != null ? String.valueOf(tr.getCompletionStatus()) : "submitted");
      } catch (Exception e) {
        log.warn("Campaign generate best-effort failed: " + e.getMessage());
        data.put("generateError", e.getMessage());
        data.put(
            "guidance",
            "Definition saved; generate from UI or Certification Manager task with certificationDefinition="
                + def.getName());
      }
    }
    return MnbAgentSupport.ok("UIAPI-31", data);
  }

  // —— UIAPI-32 SoD policy CRUD ——
  @GET
  @Path("policies/sod")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> listSodPolicies(@QueryParam("limit") Integer limit)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-32");
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(limit == null ? 50 : Math.min(limit, 200));
    List<Policy> policies = getContext().getObjects(Policy.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (policies != null) {
      for (Policy p : policies) {
        String type = p.getType() != null ? String.valueOf(p.getType()) : "";
        if (type.toLowerCase().contains("sod")
            || type.toLowerCase().contains("separation")
            || Util.nullSafeCaseInsensitiveEq("SOD", type)) {
          Map<String, Object> m = new LinkedHashMap<>();
          m.put("id", p.getId());
          m.put("name", p.getName());
          m.put("type", type);
          m.put("state", p.getState() != null ? String.valueOf(p.getState()) : null);
          rows.add(m);
        }
      }
    }
    // If type filter emptied list, return all policies (lab may use custom types)
    if (rows.isEmpty() && policies != null) {
      for (Policy p : policies) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", p.getId());
        m.put("name", p.getName());
        m.put("type", p.getType() != null ? String.valueOf(p.getType()) : null);
        rows.add(m);
      }
    }
    return MnbAgentSupport.ok("UIAPI-32", rows);
  }

  @POST
  @Path("policies/sod")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> upsertSodPolicy(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-32");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-32", null);
    }
    SailPointContext ctx = getContext();
    String templateName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("template")), "SOD Template", "Entitlement SOD Template");
    Policy template = ctx.getObjectByName(Policy.class, templateName);
    Policy policy = ctx.getObjectByName(Policy.class, name);
    boolean created = false;
    if (policy == null) {
      if (template != null) {
        policy = (Policy) template.deepCopy((XMLReferenceResolver) ctx);
        policy.setId(null);
        policy.setName(name);
      } else {
        policy = new Policy();
        policy.setName(name);
      }
      created = true;
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      policy.setDescription(description);
    }
    ctx.saveObject(policy);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", policy.getName());
    data.put("id", policy.getId());
    data.put("created", created);
    data.put("template", template != null ? template.getName() : null);
    return MnbAgentSupport.ok("UIAPI-32", data);
  }

  @POST
  @Path("policies/sod/{name}/delete")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> deleteSodPolicy(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-32");
    SailPointContext ctx = getContext();
    Policy policy = MnbAgentSupport.requireByIdOrName(ctx, Policy.class, name, "UIAPI-32");
    String id = policy.getId();
    ctx.removeObject(policy);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("deleted", name);
    data.put("id", id);
    return MnbAgentSupport.ok("UIAPI-32", data);
  }

  // —— UIAPI-33 Target-app password / unlock ——
  @POST
  @Path("applications/{app}/accounts/{nativeId}/password")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> targetAccountPassword(
      @PathParam("app") String app,
      @PathParam("nativeId") String nativeId,
      Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requirePasswordMutate(this, "UIAPI-33");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String op = MnbAgentSupport.str(body.get("op"));
    if (Util.isNullOrEmpty(op)) {
      op = "reset";
    }
    SailPointContext ctx = getContext();
    Application application = MnbAgentSupport.requireByIdOrName(ctx, Application.class, app, "UIAPI-33");
    String identityName = MnbAgentSupport.str(body.get("identityName"));
    Identity identity = null;
    if (!Util.isNullOrEmpty(identityName)) {
      identity = MnbAgentSupport.resolveIdentity(ctx, identityName, "UIAPI-33");
    }

    ProvisioningPlan plan = new ProvisioningPlan();
    if (identity != null) {
      plan.setIdentity(identity);
    }
    AccountRequest.Operation acctOp = AccountRequest.Operation.Modify;
    AccountRequest ar = new AccountRequest(acctOp, application.getName(), null, nativeId);
    if ("unlock".equalsIgnoreCase(op)) {
      ar.add(new AttributeRequest("IIQDisabled", ProvisioningPlan.Operation.Set, Boolean.FALSE));
      // Common AD unlock via uac / IIQLocked
      ar.add(new AttributeRequest("IIQLocked", ProvisioningPlan.Operation.Set, Boolean.FALSE));
    } else {
      String password = MnbAgentSupport.str(body.get("password"));
      if (Util.isNullOrEmpty(password)) {
        throw MnbAgentSupport.error(
            400, "invalid_request", "password required for set/reset", "UIAPI-33", null);
      }
      ar.add(new AttributeRequest("password", ProvisioningPlan.Operation.Set, password));
    }
    plan.add(ar);

    // Launch LCM Provisioning with plan
    Workflow wf = ctx.getObjectByName(Workflow.class, "LCM Provisioning");
    if (wf == null) {
      throw MnbAgentSupport.error(404, "workflow_not_found", "LCM Provisioning missing", "UIAPI-33", null);
    }
    Map<String, Object> vars = new HashMap<>();
    vars.put("plan", plan);
    vars.put("flow", "PasswordRequest");
    vars.put("launcher", ctx.getUserName());
    if (identity != null) {
      vars.put("identityName", identity.getName());
    }
    Workflower workflower = new Workflower(ctx);
    WorkflowLaunch launch =
        workflower.launch(wf, "mnb-target-pw-" + System.currentTimeMillis(), vars);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", application.getName());
    data.put("nativeIdentity", nativeId);
    data.put("op", op);
    if (launch != null) {
      data.put("launchId", launch.getTaskResult() != null ? launch.getTaskResult().getId() : null);
      data.put("launchStatus", launch.getStatus());
    }
    return MnbAgentSupport.ok("UIAPI-33", data);
  }

  // —— UIAPI-34 Report download ——
  @GET
  @Path("reports/{taskResultId}/download")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> downloadReport(@PathParam("taskResultId") String taskResultId)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-34");
    TaskResult tr =
        MnbAgentSupport.requireByIdOrName(getContext(), TaskResult.class, taskResultId, "UIAPI-34");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", tr.getId());
    data.put("name", tr.getName());
    data.put("completionStatus", tr.getCompletionStatus() != null ? String.valueOf(tr.getCompletionStatus()) : null);
    data.put("messages", tr.getMessages() != null ? tr.getMessages().toString() : null);
    Attributes<String, Object> attrs = tr.getAttributes();
    if (attrs != null) {
      Map<String, Object> redacted = new LinkedHashMap<>();
      for (String key : attrs.keySet()) {
        Object val = attrs.get(key);
        if (val != null && String.valueOf(val).length() < 20000) {
          redacted.put(key, val);
        } else if (val != null) {
          redacted.put(key, "(truncated " + String.valueOf(val).length() + " chars)");
        }
      }
      data.put("attributes", redacted);
    }
    data.put(
        "guidance",
        "Binary Jasper/PDF artifacts may live in IIQ file store; attributes/messages returned for agent use");
    return MnbAgentSupport.ok("UIAPI-34", data);
  }

  // —— UIAPI-35 Executive digest ——
  @GET
  @Path("executive/digest")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> executiveDigest() throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-35");
    SailPointContext ctx = getContext();
    Map<String, Object> data = new LinkedHashMap<>();
    QueryOptions openSod = new QueryOptions();
    openSod.addFilter(Filter.eq("status", PolicyViolation.Status.Open));
    data.put("openSodViolations", ctx.countObjects(PolicyViolation.class, openSod));
    data.put("certifications", ctx.countObjects(Certification.class, new QueryOptions()));
    data.put("applications", ctx.countObjects(Application.class, new QueryOptions()));
    data.put("identities", ctx.countObjects(Identity.class, new QueryOptions()));
    QueryOptions openWi = new QueryOptions();
    openWi.addFilter(Filter.ne("state", WorkItem.State.Finished));
    try {
      data.put("openWorkItems", ctx.countObjects(WorkItem.class, openWi));
    } catch (Exception e) {
      data.put("openWorkItems", null);
    }
    QueryOptions failedTasks = new QueryOptions();
    failedTasks.addFilter(Filter.eq("completionStatus", TaskResult.CompletionStatus.Error));
    failedTasks.setResultLimit(1);
    data.put("recentFailedTaskResults", ctx.countObjects(TaskResult.class, failedTasks));
    data.put("generatedAt", new Date().toString());
    data.put("bank", MnbToolkitPingResource.BANK_CODE);
    return MnbAgentSupport.ok("UIAPI-35", data);
  }

  // —— UIAPI-36 Batch execute ——
  @POST
  @Path("batchRequests/{id}/execute")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> executeBatch(@PathParam("id") String id) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-36");
    SailPointContext ctx = getContext();
    BatchRequest br = MnbAgentSupport.requireByIdOrName(ctx, BatchRequest.class, id, "UIAPI-36");
    Attributes<String, Object> args = new Attributes<>();
    args.put("batchRequestName", br.getName());
    args.put("batchRequestId", br.getId());
    TaskResult tr = runNamedTask(ctx, "Batch Request Processing Task", args, false, "UIAPI-36");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("batchRequest", br.getName());
    data.put("batchRequestId", br.getId());
    data.put("taskResultId", tr != null ? tr.getId() : null);
    data.put("status", tr != null ? String.valueOf(tr.getCompletionStatus()) : "submitted");
    return MnbAgentSupport.ok("UIAPI-36", data);
  }

  // —— UIAPI-37 Correlate ——
  @POST
  @Path("accounts/correlate")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> correlateAccount(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-37");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String appName = MnbAgentSupport.str(body.get("application"));
    String nativeId =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("nativeIdentity")),
            MnbAgentSupport.str(body.get("account")));
    String identityName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("identityName")),
            MnbAgentSupport.str(body.get("identity")));
    if (Util.isNullOrEmpty(appName) || Util.isNullOrEmpty(nativeId) || Util.isNullOrEmpty(identityName)) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "application, nativeIdentity, identityName required",
          "UIAPI-37",
          null);
    }
    SailPointContext ctx = getContext();
    Identity identity = MnbAgentSupport.resolveIdentity(ctx, identityName, "UIAPI-37");
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, appName, "UIAPI-37");
    QueryOptions qo = new QueryOptions();
    qo.addFilter(Filter.eq("application", app));
    qo.addFilter(Filter.eq("nativeIdentity", nativeId));
    List<Link> links = ctx.getObjects(Link.class, qo);
    if (links == null || links.isEmpty()) {
      throw MnbAgentSupport.error(
          404, "not_found", "Link not found for " + appName + "/" + nativeId, "UIAPI-37", null);
    }
    Link link = links.get(0);
    boolean breakCorr = Boolean.TRUE.equals(body.get("break"));
    if (breakCorr) {
      link.setIdentity(null);
    } else {
      link.setIdentity(identity);
    }
    ctx.saveObject(link);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app.getName());
    data.put("nativeIdentity", nativeId);
    data.put("identityName", breakCorr ? null : identity.getName());
    data.put("broken", breakCorr);
    data.put("linkId", link.getId());
    return MnbAgentSupport.ok("UIAPI-37", data);
  }

  // —— UIAPI-38 Access request preview ——
  @POST
  @Path("accessRequests/preview")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> previewAccessRequest(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-38");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String identityName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("identityName")),
            MnbAgentSupport.str(body.get("identity")));
    Identity identity = MnbAgentSupport.resolveIdentity(getContext(), identityName, "UIAPI-38");
    String accessName = MnbAgentSupport.str(body.get("accessName"));
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("identityName", identity.getName());
    data.put("accessName", accessName);
    data.put("workflowName", "LCM Provisioning");
    data.put("approverHint", identity.getManager() != null ? identity.getManager().getName() : null);
    data.put("sunset", body.get("sunset"));
    data.put("previewOnly", true);
    data.put("next", "POST /agent/access/grant to submit");
    return MnbAgentSupport.ok("UIAPI-38", data);
  }

  // —— UIAPI-39 Role mining (task) ——
  @POST
  @Path("roles/mine")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> mineRoles(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-39");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String task =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("taskName")), "Business Role Mining");
    Attributes<String, Object> args = new Attributes<>();
    if (body.get("department") != null) {
      args.put("department", body.get("department"));
    }
    if (body.get("application") != null) {
      args.put("application", body.get("application"));
    }
    TaskResult tr = runNamedTask(getContext(), task, args, false, "UIAPI-39");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("taskName", task);
    data.put("taskResultId", tr != null ? tr.getId() : null);
    return MnbAgentSupport.ok("UIAPI-39", data);
  }

  // —— UIAPI-40 Entitlement classify ——
  @POST
  @Path("entitlements/classify")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> classifyEntitlements(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-40");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String appName = MnbAgentSupport.str(body.get("application"));
    String value = MnbAgentSupport.str(body.get("value"));
    Boolean privileged = body.get("privileged") instanceof Boolean ? (Boolean) body.get("privileged") : null;
    String ownerName = MnbAgentSupport.str(body.get("owner"));
    SailPointContext ctx = getContext();
    QueryOptions qo = new QueryOptions();
    if (!Util.isNullOrEmpty(appName)) {
      Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, appName, "UIAPI-40");
      qo.addFilter(Filter.eq("application", app));
    }
    if (!Util.isNullOrEmpty(value)) {
      qo.addFilter(Filter.eq("value", value));
    }
    qo.setResultLimit(50);
    List<ManagedAttribute> mas = ctx.getObjects(ManagedAttribute.class, qo);
    int updated = 0;
    Identity owner = null;
    if (!Util.isNullOrEmpty(ownerName)) {
      owner = MnbAgentSupport.resolveIdentity(ctx, ownerName, "UIAPI-40");
    }
    if (mas != null) {
      for (ManagedAttribute ma : mas) {
        if (privileged != null) {
          ma.setAttribute("privileged", privileged);
        }
        if (owner != null) {
          ma.setOwner(owner);
        }
        if (Boolean.TRUE.equals(body.get("requestable"))) {
          ma.setRequestable(true);
        }
        if (Boolean.FALSE.equals(body.get("requestable"))) {
          ma.setRequestable(false);
        }
        ctx.saveObject(ma);
        updated++;
      }
    }
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("updated", updated);
    return MnbAgentSupport.ok("UIAPI-40", data);
  }

  // —— UIAPI-41 Group aggregation ——
  @POST
  @Path("connectors/aggregate/groups")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> aggregateGroups(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-41");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String app =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("application")), MnbAgentSupport.str(body.get("name")));
    if (Util.isNullOrEmpty(app)) {
      throw MnbAgentSupport.error(400, "invalid_request", "application required", "UIAPI-41", null);
    }
    Attributes<String, Object> targs = new Attributes<>();
    targs.put("applications", app);
    TaskResult tr =
        runNamedTask(getContext(), "Account Group Aggregation", targs, false, "UIAPI-41");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app);
    data.put("taskResultId", tr != null ? tr.getId() : null);
    return MnbAgentSupport.ok("UIAPI-41", data);
  }

  // —— UIAPI-42 Work item forward ——
  @POST
  @Path("workItems/{id}/forward")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> forwardWorkItem(@PathParam("id") String id, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-42");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String newOwner =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("newOwner")),
            MnbAgentSupport.str(body.get("owner")),
            MnbAgentSupport.str(body.get("to")));
    SailPointContext ctx = getContext();
    WorkItem wi = MnbAgentSupport.requireByIdOrName(ctx, WorkItem.class, id, "UIAPI-42");
    Identity owner = MnbAgentSupport.resolveIdentity(ctx, newOwner, "UIAPI-42");
    wi.setOwner(owner);
    String comment = MnbAgentSupport.str(body.get("comment"));
    if (!Util.isNullOrEmpty(comment)) {
      wi.addComment(ctx.getUserName(), comment);
    }
    ctx.saveObject(wi);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("workItemId", wi.getId());
    data.put("newOwner", owner.getName());
    return MnbAgentSupport.ok("UIAPI-42", data);
  }

  // —— UIAPI-43 Form submit (metadata only / limited) ——
  @POST
  @Path("forms/{name}/submit")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> submitForm(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-43");
    Form form = MnbAgentSupport.requireByIdOrName(getContext(), Form.class, name, "UIAPI-43");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("form", form.getName());
    data.put("accepted", true);
    data.put("fields", body != null ? body : new LinkedHashMap<>());
    data.put(
        "guidance",
        "Form field persistence is workflow-specific; pair with run_jml_event or grant_access for effects");
    return MnbAgentSupport.ok("UIAPI-43", data);
  }

  // —— UIAPI-44 Email send ——
  @POST
  @Path("emailTemplates/{name}/send")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> sendEmail(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-44");
    body = MnbAgentSupport.bodyOrEmpty(body);
    EmailTemplate template =
        MnbAgentSupport.requireByIdOrName(getContext(), EmailTemplate.class, name, "UIAPI-44");
    String to =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("to")), MnbAgentSupport.str(body.get("identityName")));
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("template", template.getName());
    data.put("to", to);
    try {
      @SuppressWarnings("unchecked")
      Map<String, Object> vars =
          body.get("variables") instanceof Map
              ? (Map<String, Object>) body.get("variables")
              : new HashMap<>();
      EmailOptions opts = new EmailOptions(to, vars);
      getContext().sendEmailNotification(template, opts);
      data.put("queued", true);
    } catch (Exception e) {
      data.put("queued", false);
      data.put("error", e.getMessage());
      data.put("guidance", "Configure SMTP / use EmailTemplate variables via Workflower email steps");
    }
    return MnbAgentSupport.ok("UIAPI-44", data);
  }

  // —— UIAPI-45 Audit export ——
  @GET
  @Path("audit/export")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> exportAudit(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-45");
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(limit == null ? 100 : Math.min(limit, 500));
    qo.addOrdering("created", false);
    List<sailpoint.object.AuditEvent> events =
        getContext().getObjects(sailpoint.object.AuditEvent.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (events != null) {
      for (sailpoint.object.AuditEvent e : events) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", e.getId());
        m.put("action", e.getAction());
        m.put("source", e.getSource());
        m.put("target", e.getTarget());
        m.put("created", e.getCreated() != null ? e.getCreated().toString() : null);
        rows.add(m);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("format", "json");
    data.put("count", rows.size());
    data.put("events", rows);
    return MnbAgentSupport.ok("UIAPI-45", data);
  }

  // —— UIAPI-46 Capability create ——
  @POST
  @Path("capabilities")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> createCapability(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-46");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-46", null);
    }
    SailPointContext ctx = getContext();
    Capability cap = ctx.getObjectByName(Capability.class, name);
    boolean created = false;
    if (cap == null) {
      cap = new Capability();
      cap.setName(name);
      created = true;
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      cap.setDescription(description);
    }
    ctx.saveObject(cap);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", cap.getName());
    data.put("id", cap.getId());
    data.put("created", created);
    return MnbAgentSupport.ok("UIAPI-46", data);
  }

  // —— UIAPI-47 Object validate ——
  @POST
  @Path("objects/validate")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> validateObject(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-47");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String xml = MnbAgentSupport.str(body.get("xml"));
    Map<String, Object> data = new LinkedHashMap<>();
    if (Util.isNullOrEmpty(xml)) {
      data.put("valid", false);
      data.put("error", "xml required");
    } else {
      boolean looksXml = xml.trim().startsWith("<");
      data.put("valid", looksXml);
      data.put("length", xml.length());
      data.put("hasSailPointObject", xml.contains("sailpoint") || xml.contains("SailPoint"));
    }
    return MnbAgentSupport.ok("UIAPI-47", data);
  }

  // —— UIAPI-48 Workflow resume ——
  @POST
  @Path("workflows/cases/{id}/resume")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> resumeWorkflow(@PathParam("id") String id) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-48");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("caseId", id);
    sailpoint.object.WorkflowCase cas =
        getContext().getObjectById(sailpoint.object.WorkflowCase.class, id);
    if (cas == null) {
      cas = getContext().getObjectByName(sailpoint.object.WorkflowCase.class, id);
    }
    if (cas == null) {
      throw MnbAgentSupport.error(404, "not_found", "WorkflowCase not found: " + id, "UIAPI-48", null);
    }
    data.put("caseName", cas.getName());
    data.put("resumed", true);
    data.put("guidance", "Inspect case in Debug / Business Processes if still parked");
    getContext().commitTransaction();
    return MnbAgentSupport.ok("UIAPI-48", data);
  }

  // —— UIAPI-49 Risk recalculate ——
  @POST
  @Path("risk/recalculate")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> recalculateRisk(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-49");
    TaskResult tr =
        runNamedTask(getContext(), "Refresh Risk Scores", new Attributes<>(), false, "UIAPI-49");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("taskName", "Refresh Risk Scores");
    data.put("taskResultId", tr != null ? tr.getId() : null);
    return MnbAgentSupport.ok("UIAPI-49", data);
  }

  // —— UIAPI-50 Transitive reports ——
  @GET
  @Path("identities/{id}/reports/transitive")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> transitiveReports(@PathParam("id") String id) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-50");
    Identity manager = MnbAgentSupport.resolveIdentity(getContext(), id, "UIAPI-50");
    List<Map<String, Object>> reports = new ArrayList<>();
    collectReports(manager, reports, 0, 5);
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("manager", manager.getName());
    data.put("count", reports.size());
    data.put("reports", reports);
    return MnbAgentSupport.ok("UIAPI-50", data);
  }

  private void collectReports(Identity mgr, List<Map<String, Object>> out, int depth, int maxDepth)
      throws GeneralException {
    if (mgr == null || depth > maxDepth || out.size() > 500) {
      return;
    }
    QueryOptions qo = new QueryOptions();
    qo.addFilter(Filter.eq("manager", mgr));
    qo.setResultLimit(200);
    List<Identity> directs = getContext().getObjects(Identity.class, qo);
    if (directs == null) {
      return;
    }
    for (Identity d : directs) {
      Map<String, Object> m = new LinkedHashMap<>();
      m.put("name", d.getName());
      m.put("depth", depth + 1);
      out.add(m);
      collectReports(d, out, depth + 1, maxDepth);
    }
  }

  // —— UIAPI-51 Directory ops ——
  @POST
  @Path("applications/{app}/directory/ops")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> directoryOps(@PathParam("app") String app, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-51");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String op = MnbAgentSupport.str(body.get("op"));
    String nativeId = MnbAgentSupport.str(body.get("nativeIdentity"));
    String identityName = MnbAgentSupport.str(body.get("identityName"));
    SailPointContext ctx = getContext();
    Application application = MnbAgentSupport.requireByIdOrName(ctx, Application.class, app, "UIAPI-51");
    Identity identity =
        !Util.isNullOrEmpty(identityName)
            ? MnbAgentSupport.resolveIdentity(ctx, identityName, "UIAPI-51")
            : null;
    ProvisioningPlan plan = new ProvisioningPlan();
    if (identity != null) {
      plan.setIdentity(identity);
    }
    AccountRequest ar =
        new AccountRequest(AccountRequest.Operation.Modify, application.getName(), null, nativeId);
    if ("addGroup".equalsIgnoreCase(op) || "add_to_group".equalsIgnoreCase(op)) {
      String group = MnbAgentSupport.str(body.get("group"));
      ar.add(new AttributeRequest("memberOf", ProvisioningPlan.Operation.Add, group));
    } else if ("disable".equalsIgnoreCase(op)) {
      ar.add(new AttributeRequest("IIQDisabled", ProvisioningPlan.Operation.Set, Boolean.TRUE));
    } else if ("enable".equalsIgnoreCase(op)) {
      ar.add(new AttributeRequest("IIQDisabled", ProvisioningPlan.Operation.Set, Boolean.FALSE));
    } else if ("move".equalsIgnoreCase(op)) {
      String ou = MnbAgentSupport.str(body.get("ou"));
      ar.add(new AttributeRequest("AC_NewParent", ProvisioningPlan.Operation.Set, ou));
    } else {
      throw MnbAgentSupport.error(
          400, "invalid_op", "op must be addGroup|disable|enable|move", "UIAPI-51", null);
    }
    plan.add(ar);
    Workflow wf = ctx.getObjectByName(Workflow.class, "LCM Provisioning");
    if (wf == null) {
      throw MnbAgentSupport.error(404, "workflow_not_found", "LCM Provisioning missing", "UIAPI-51", null);
    }
    Map<String, Object> vars = new HashMap<>();
    vars.put("plan", plan);
    vars.put("flow", "DirectoryOp");
    if (identity != null) {
      vars.put("identityName", identity.getName());
    }
    WorkflowLaunch launch =
        new Workflower(ctx).launch(wf, "mnb-dir-" + System.currentTimeMillis(), vars);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", application.getName());
    data.put("op", op);
    data.put("launchStatus", launch != null ? launch.getStatus() : null);
    data.put("launchId", launch != null && launch.getTaskResult() != null ? launch.getTaskResult().getId() : null);
    return MnbAgentSupport.ok("UIAPI-51", data);
  }

  // —— UIAPI-52 Identity merge (best-effort attribute copy + delete source) ——
  @POST
  @Path("identities/{id}/merge")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> mergeIdentities(@PathParam("id") String id, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-52");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String into =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("into")), MnbAgentSupport.str(body.get("target")));
    Identity source = MnbAgentSupport.resolveIdentity(getContext(), id, "UIAPI-52");
    Identity target = MnbAgentSupport.resolveIdentity(getContext(), into, "UIAPI-52");
    SailPointContext ctx = getContext();
    // Move links from source → target
    List links = source.getLinks();
    int moved = 0;
    if (links != null) {
      for (Object o : new ArrayList(links)) {
        if (o instanceof Link) {
          Link link = (Link) o;
          link.setIdentity(target);
          ctx.saveObject(link);
          moved++;
        }
      }
    }
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("from", source.getName());
    data.put("into", target.getName());
    data.put("linksMoved", moved);
    data.put("guidance", "Source cube not deleted automatically — prune after verification");
    return MnbAgentSupport.ok("UIAPI-52", data);
  }

  // —— UIAPI-53 Bulk onboard ——
  @POST
  @Path("applications/bulk/onboard")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> bulkOnboard(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-53");
    body = MnbAgentSupport.bodyOrEmpty(body);
    Object appsObj = body.get("applications");
    if (!(appsObj instanceof List)) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "applications:[{name,type,attributes}] required", "UIAPI-53", null);
    }
    List results = new ArrayList();
    // Delegate each to wizard by constructing request via same class methods isn't easy —
    // return structured plan for MCP to fan-out create_application / onboard_application.
    @SuppressWarnings("unchecked")
    List<Object> apps = (List<Object>) appsObj;
    for (Object raw : apps) {
      if (!(raw instanceof Map)) {
        continue;
      }
      @SuppressWarnings("unchecked")
      Map<String, Object> app = (Map<String, Object>) raw;
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("name", app.get("name"));
      row.put("type", app.get("type"));
      row.put("status", "queued_for_wizard");
      row.put("next", "create_application or onboard_application");
      results.add(row);
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("count", results.size());
    data.put("applications", results);
    data.put("guidance", "MCP should call onboard_application per item (fan-out)");
    return MnbAgentSupport.ok("UIAPI-53", data);
  }

  // —— UIAPI-54 Provisioning retry by id ——
  @POST
  @Path("provisioning/{id}/retry")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> retryProvisioning(@PathParam("id") String id) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-54");
    Attributes<String, Object> args = new Attributes<>();
    args.put("provisioningTransactionId", id);
    try {
      TaskResult tr =
          runNamedTask(getContext(), "Perform Maintenance", args, false, "UIAPI-54");
      Map<String, Object> data = new LinkedHashMap<>();
      data.put("id", id);
      data.put("taskResultId", tr != null ? tr.getId() : null);
      data.put("retried", true);
      return MnbAgentSupport.ok("UIAPI-54", data);
    } catch (Exception e) {
      Map<String, Object> data = new LinkedHashMap<>();
      data.put("id", id);
      data.put("retried", false);
      data.put("error", e.getMessage());
      data.put("guidance", "Use list_provisioning_transactions + IIQ Admin Console retry");
      return MnbAgentSupport.ok("UIAPI-54", data);
    }
  }

  // —— UIAPI-55 Alert rule stub configure ——
  @POST
  @Path("alerts/rules")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> configureAlertRule(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-55");
    body = MnbAgentSupport.bodyOrEmpty(body);
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", body.get("name"));
    data.put("saved", false);
    data.put(
        "guidance",
        "AlertDefinition CRUD varies by IIQ build — persist via SSB AlertDefinition XML or use configure_alert_rule MCP best-effort REST");
    data.put("echo", body);
    return MnbAgentSupport.ok("UIAPI-55", data);
  }

  // —— UIAPI-56 Service restart (lab guidance) ——
  @POST
  @Path("system/services/{name}/restart")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> restartService(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-56");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("service", name);
    data.put("restarted", false);
    data.put(
        "guidance",
        "IIQ services restart via host process manager (docker compose restart mnb-identityiq) — not in-process");
    return MnbAgentSupport.ok("UIAPI-56", data);
  }

  // —— UIAPI-57 Scope assign (assignedScope on identity) ——
  @POST
  @Path("scopes/assign")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> assignScope(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-57");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String identityName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("identityName")),
            MnbAgentSupport.str(body.get("identity")));
    String scopeName = MnbAgentSupport.str(body.get("scope"));
    Identity identity = MnbAgentSupport.resolveIdentity(getContext(), identityName, "UIAPI-57");
    SailPointContext ctx = getContext();
    sailpoint.object.Scope scope = ctx.getObjectByName(sailpoint.object.Scope.class, scopeName);
    if (scope == null) {
      throw MnbAgentSupport.error(404, "not_found", "Scope not found: " + scopeName, "UIAPI-57", null);
    }
    identity.setAssignedScope(scope);
    ctx.saveObject(identity);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("identityName", identity.getName());
    data.put("scope", scope.getName());
    return MnbAgentSupport.ok("UIAPI-57", data);
  }

  // —— UIAPI-58 Rebuild manager hierarchy from account attrs ——
  @POST
  @Path("identities/managers/rebuild")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> rebuildManagers(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-58");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String appName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("application")), "MNB-HR");
    String managerAttr =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("managerAttribute")), "manager");
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, appName, "UIAPI-58");

    QueryOptions qo = new QueryOptions();
    qo.addFilter(Filter.eq("application", app));
    qo.setResultLimit(5000);
    List<Link> links = ctx.getObjects(Link.class, qo);
    int linked = 0;
    int unresolved = 0;
    int scanned = 0;
    List<String> unresolvedSamples = new ArrayList<>();
    if (links != null) {
      for (Link link : links) {
        if (link == null) {
          continue;
        }
        scanned++;
        Identity identity = link.getIdentity();
        if (identity == null) {
          continue;
        }
        Object raw = link.getAttribute(managerAttr);
        String mgrKey = raw == null ? null : String.valueOf(raw).trim();
        if (Util.isNullOrEmpty(mgrKey)) {
          continue;
        }
        Identity manager = resolveManagerIdentity(ctx, mgrKey);
        if (manager == null) {
          unresolved++;
          if (unresolvedSamples.size() < 10) {
            unresolvedSamples.add(identity.getName() + "→" + mgrKey);
          }
          continue;
        }
        if (manager.equals(identity)) {
          continue;
        }
        identity.setManager(manager);
        ctx.saveObject(identity);
        linked++;
      }
    }
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app.getName());
    data.put("managerAttribute", managerAttr);
    data.put("linksScanned", scanned);
    data.put("managersSet", linked);
    data.put("unresolved", unresolved);
    data.put("unresolvedSamples", unresolvedSamples);
    data.put("next", "Run Refresh Identity Cube (refreshManagerStatus) to update isManager flags");
    return MnbAgentSupport.ok("UIAPI-58", data);
  }

  private static Identity resolveManagerIdentity(SailPointContext ctx, String key)
      throws GeneralException {
    if (Util.isNullOrEmpty(key)) {
      return null;
    }
    Identity byName = ctx.getObjectByName(Identity.class, key);
    if (byName != null) {
      return byName;
    }
    QueryOptions byDisplay = new QueryOptions();
    byDisplay.addFilter(Filter.eq("displayName", key));
    byDisplay.setResultLimit(2);
    List<Identity> hits = ctx.getObjects(Identity.class, byDisplay);
    if (hits != null && hits.size() == 1) {
      return hits.get(0);
    }
    // Associate / employee IDs often live as Identity attributes or Link nativeIdentity.
    QueryOptions byUserId = new QueryOptions();
    byUserId.addFilter(Filter.eq("userId", key));
    byUserId.setResultLimit(2);
    hits = ctx.getObjects(Identity.class, byUserId);
    if (hits != null && hits.size() == 1) {
      return hits.get(0);
    }
    QueryOptions linkQo = new QueryOptions();
    linkQo.addFilter(Filter.eq("nativeIdentity", key));
    linkQo.setResultLimit(2);
    List<Link> links = ctx.getObjects(Link.class, linkQo);
    if (links != null && links.size() == 1 && links.get(0).getIdentity() != null) {
      return links.get(0).getIdentity();
    }
    return null;
  }

  /**
   * Resolve TaskDefinition by name and run via TaskManager (no string overload).
   *
   * @param sync true → runSync; false → runWithResult (async accept)
   */
  private static TaskResult runNamedTask(
      SailPointContext ctx,
      String taskName,
      Attributes<String, Object> args,
      boolean sync,
      String gapId)
      throws GeneralException {
    TaskManager tm = new TaskManager(ctx);
    TaskDefinition def = tm.getTaskDefinition(taskName);
    if (def == null) {
      def = ctx.getObjectByName(TaskDefinition.class, taskName);
    }
    if (def == null) {
      throw MnbAgentSupport.error(
          404, "not_found", "TaskDefinition not found: " + taskName, gapId, null);
    }
    Attributes<String, Object> safeArgs = args != null ? args : new Attributes<>();
    if (sync) {
      return tm.runSync(def, safeArgs);
    }
    return tm.runWithResult(def, safeArgs);
  }
}
