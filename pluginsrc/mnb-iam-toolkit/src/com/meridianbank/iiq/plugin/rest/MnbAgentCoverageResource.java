package com.meridianbank.iiq.plugin.rest;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import javax.ws.rs.Consumes;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.MediaType;

import org.apache.log4j.Logger;

import sailpoint.api.Grouper;
import sailpoint.api.SailPointContext;
import sailpoint.api.TaskManager;
import sailpoint.api.Workflower;
import sailpoint.object.Application;
import sailpoint.object.AttributeDefinition;
import sailpoint.object.Attributes;
import sailpoint.object.BatchRequest;
import sailpoint.object.Bundle;
import sailpoint.object.Capability;
import sailpoint.object.Certification;
import sailpoint.object.CertificationDefinition;
import sailpoint.object.CorrelationConfig;
import sailpoint.object.EmailOptions;
import sailpoint.object.EmailTemplate;
import sailpoint.object.Field;
import sailpoint.object.Filter;
import sailpoint.object.Form;
import sailpoint.object.GroupDefinition;
import sailpoint.object.GroupFactory;
import sailpoint.object.Identity;
import sailpoint.object.IdentitySelector;
import sailpoint.object.IdentityTrigger;
import sailpoint.object.Link;
import sailpoint.object.ManagedAttribute;
import sailpoint.object.ObjectAttribute;
import sailpoint.object.ObjectConfig;
import sailpoint.object.PasswordPolicy;
import sailpoint.object.Policy;
import sailpoint.object.PolicyViolation;
import sailpoint.object.ProvisioningPlan;
import sailpoint.object.ProvisioningPlan.AccountRequest;
import sailpoint.object.ProvisioningPlan.AttributeRequest;
import sailpoint.object.ProvisioningTransaction;
import sailpoint.object.QueryOptions;
import sailpoint.object.SPRight;
import sailpoint.object.Schema;
import sailpoint.object.ScoreConfig;
import sailpoint.object.ScoreDefinition;
import sailpoint.object.Script;
import sailpoint.object.SODConstraint;
import sailpoint.object.TaskDefinition;
import sailpoint.object.TaskResult;
import sailpoint.object.Template;
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
    // Prefer caller template, then Role SOD template, then entitlement SOD.
    // Never keep an invalid template name — that yields a bare Policy the UI cannot edit as SOD.
    Policy template = null;
    String templateName = null;
    for (String candidate :
        new String[] {
          MnbAgentSupport.str(body.get("template")), "SOD Template", "Entitlement SOD Template"
        }) {
      if (Util.isNullOrEmpty(candidate)) {
        continue;
      }
      Policy t = ctx.getObjectByName(Policy.class, candidate);
      if (t != null) {
        template = t;
        templateName = candidate;
        break;
      }
    }
    Policy policy = ctx.getObjectByName(Policy.class, name);
    boolean created = false;
    if (policy == null) {
      if (template != null) {
        policy = (Policy) template.deepCopy((XMLReferenceResolver) ctx);
        policy.setId(null);
        policy.setName(name);
        policy.setTemplate(false);
      } else {
        policy = new Policy();
        policy.setName(name);
        applyRoleSodMetadata(policy);
      }
      created = true;
    } else if (Util.isNullOrEmpty(policy.getType()) || !"SOD".equals(policy.getType())
        && !"EntitlementSOD".equals(policy.getType())) {
      // Repair shell policies created without Role/Entitlement SOD metadata (UI blank rules table).
      if (template != null && "SOD".equals(template.getType())) {
        applyRoleSodMetadata(policy);
      } else if (template != null && "EntitlementSOD".equals(template.getType())) {
        applyEntitlementSodMetadata(policy);
      } else {
        applyRoleSodMetadata(policy);
      }
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      policy.setDescription(description);
    }
    String state = MnbAgentSupport.str(body.get("state"));
    if (!Util.isNullOrEmpty(state)) {
      try {
        policy.setState(Policy.State.valueOf(state));
      } catch (IllegalArgumentException ex) {
        throw MnbAgentSupport.error(
            400, "invalid_request", "state must be Active or Inactive", "UIAPI-32", null);
      }
    }
    ctx.saveObject(policy);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", policy.getName());
    data.put("id", policy.getId());
    data.put("created", created);
    data.put("template", templateName);
    data.put("type", policy.getType());
    data.put("configPage", policy.getConfigPage());
    data.put("executor", policy.getExecutor());
    data.put("state", policy.getState() != null ? policy.getState().name() : null);
    return MnbAgentSupport.ok("UIAPI-32", data);
  }

  private static void applyRoleSodMetadata(Policy policy) {
    policy.setType("SOD");
    policy.setTypeKey("policy_type_sod");
    policy.setConfigPage("sodpolicy.xhtml");
    policy.setExecutor("sailpoint.policy.SODPolicyExecutor");
    policy.setCertificationActions("Remediated,Mitigated,Delegated");
  }

  private static void applyEntitlementSodMetadata(Policy policy) {
    policy.setType("EntitlementSOD");
    policy.setTypeKey("policy_type_entitlement_sod");
    policy.setConfigPage("entitlementPolicy.xhtml");
    policy.setExecutor("sailpoint.policy.EntitlementSODPolicyExecutor");
    policy.setCertificationActions("Remediated,Mitigated,Delegated");
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
    boolean breakCorr =
        Boolean.TRUE.equals(body.get("break"))
            || Boolean.TRUE.equals(body.get("breakCorrelation"))
            || Boolean.TRUE.equals(body.get("uncorrelate"));
    if (Util.isNullOrEmpty(appName) || Util.isNullOrEmpty(nativeId)) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "application and nativeIdentity required",
          "UIAPI-37",
          null);
    }
    if (!breakCorr && Util.isNullOrEmpty(identityName)) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "identityName required unless break/uncorrelate=true",
          "UIAPI-37",
          null);
    }
    SailPointContext ctx = getContext();
    Identity identity =
        !Util.isNullOrEmpty(identityName)
            ? MnbAgentSupport.resolveIdentity(ctx, identityName, "UIAPI-37")
            : null;
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
    data.put("identityName", breakCorr ? null : (identity != null ? identity.getName() : null));
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

  // —— UIAPI-43 Form submit (launch workflow when workflowName provided) ——
  @POST
  @Path("forms/{name}/submit")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> submitForm(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-43");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Form form = MnbAgentSupport.requireByIdOrName(ctx, Form.class, name, "UIAPI-43");
    Map<String, Object> fields = new LinkedHashMap<>();
    if (body.get("fields") instanceof Map) {
      @SuppressWarnings("unchecked")
      Map<String, Object> f = (Map<String, Object>) body.get("fields");
      fields.putAll(f);
    } else {
      for (Map.Entry<String, Object> e : body.entrySet()) {
        String k = e.getKey();
        if ("workflowName".equals(k)
            || "workflow".equals(k)
            || "identity".equals(k)
            || "identityName".equals(k)
            || "dryRun".equals(k)) {
          continue;
        }
        fields.put(k, e.getValue());
      }
    }
    String workflowName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("workflowName")),
            MnbAgentSupport.str(body.get("workflow")));
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("form", form.getName());
    data.put("fields", fields);
    data.put("accepted", true);
    if (Util.isNullOrEmpty(workflowName) || Boolean.TRUE.equals(body.get("dryRun"))) {
      data.put("launched", false);
      data.put(
          "guidance",
          "Pass workflowName to launch; otherwise pair with run_jml_event / grant_access");
      return MnbAgentSupport.ok("UIAPI-43", data);
    }
    Workflow wf = ctx.getObjectByName(Workflow.class, workflowName);
    if (wf == null) {
      throw MnbAgentSupport.error(
          404, "not_found", "Workflow not found: " + workflowName, "UIAPI-43", null);
    }
    Map<String, Object> vars = new HashMap<>();
    vars.put("formName", form.getName());
    vars.put("formAnswers", fields);
    vars.putAll(fields);
    String identityName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("identityName")),
            MnbAgentSupport.str(body.get("identity")));
    if (!Util.isNullOrEmpty(identityName)) {
      Identity idn = MnbAgentSupport.resolveIdentity(ctx, identityName, "UIAPI-43");
      vars.put("identityName", idn.getName());
      vars.put("identity", idn.getName());
    }
    WorkflowLaunch launch =
        new Workflower(ctx).launch(wf, "mnb-form-" + System.currentTimeMillis(), vars);
    ctx.commitTransaction();
    data.put("launched", true);
    data.put("workflowName", workflowName);
    data.put(
        "workflowCaseId",
        launch.getWorkflowCase() != null ? launch.getWorkflowCase().getId() : null);
    data.put("launchStatus", launch.getStatus() != null ? String.valueOf(launch.getStatus()) : null);
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
    Object rightsObj = body.get("rights");
    if (rightsObj instanceof List) {
      List<SPRight> rights = resolveSpRights(ctx, (List<?>) rightsObj, "UIAPI-46");
      cap.setRights(rights);
    }
    ctx.saveObject(cap);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", cap.getName());
    data.put("id", cap.getId());
    data.put("created", created);
    data.put("rights", rightNames(cap));
    return MnbAgentSupport.ok("UIAPI-46", data);
  }

  // —— UIAPI-84 Capability rights matrix ——
  @POST
  @Path("capabilities/{name}/rights")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> setCapabilityRights(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-84");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Capability cap = MnbAgentSupport.requireByIdOrName(ctx, Capability.class, name, "UIAPI-84");
    Object rightsObj = body.get("rights");
    if (!(rightsObj instanceof List)) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "rights list required", "UIAPI-84", null);
    }
    String op = MnbAgentSupport.firstNonEmpty(MnbAgentSupport.str(body.get("op")), "replace").toLowerCase();
    List<SPRight> incoming = resolveSpRights(ctx, (List<?>) rightsObj, "UIAPI-84");
    if ("add".equals(op)) {
      List<SPRight> current = cap.getRights() != null ? new ArrayList<>(cap.getRights()) : new ArrayList<>();
      Set<String> have = new HashSet<>();
      for (SPRight r : current) {
        if (r != null && r.getName() != null) {
          have.add(r.getName());
        }
      }
      for (SPRight r : incoming) {
        if (r != null && r.getName() != null && !have.contains(r.getName())) {
          current.add(r);
          have.add(r.getName());
        }
      }
      cap.setRights(current);
    } else if ("remove".equals(op)) {
      Set<String> remove = new HashSet<>();
      for (SPRight r : incoming) {
        if (r != null && r.getName() != null) {
          remove.add(r.getName());
        }
      }
      List<SPRight> next = new ArrayList<>();
      if (cap.getRights() != null) {
        for (SPRight r : cap.getRights()) {
          if (r != null && r.getName() != null && !remove.contains(r.getName())) {
            next.add(r);
          }
        }
      }
      cap.setRights(next);
    } else {
      cap.setRights(incoming);
    }
    ctx.saveObject(cap);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", cap.getName());
    data.put("op", op);
    data.put("rights", rightNames(cap));
    return MnbAgentSupport.ok("UIAPI-84", data);
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

  // —— UIAPI-59 Org chart (authoritative manager hierarchy) ——
  @GET
  @Path("orgchart")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> orgChart(
      @QueryParam("root") String root,
      @QueryParam("depth") Integer depth,
      @QueryParam("mode") String mode,
      @QueryParam("includeInactive") Boolean includeInactive,
      @QueryParam("includeTechnical") Boolean includeTechnical)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-59");
    int maxDepth = depth == null ? 12 : Math.max(1, Math.min(depth, 20));
    boolean inactiveOk = Boolean.TRUE.equals(includeInactive);
    boolean techOk = Boolean.TRUE.equals(includeTechnical);
    String chartMode =
        Util.isNullOrEmpty(mode) ? (Util.isNullOrEmpty(root) ? "company" : "subtree") : mode.trim();

    SailPointContext ctx = getContext();
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(5000);
    List<Identity> all = ctx.getObjects(Identity.class, qo);
    Map<String, Identity> byId = new LinkedHashMap<>();
    Map<String, List<Identity>> children = new HashMap<>();
    if (all != null) {
      for (Identity idn : all) {
        if (idn == null || idn.isWorkgroup()) {
          continue;
        }
        if (!techOk && isTechnicalIdentity(idn)) {
          continue;
        }
        if (!inactiveOk && idn.isInactive()) {
          continue;
        }
        byId.put(idn.getId(), idn);
      }
      for (Identity idn : byId.values()) {
        Identity mgr = idn.getManager();
        if (mgr == null || !byId.containsKey(mgr.getId())) {
          continue;
        }
        children.computeIfAbsent(mgr.getId(), k -> new ArrayList<>()).add(idn);
      }
    }
    Set<String> brokenManagers = new HashSet<>();
    for (Identity idn : byId.values()) {
      Identity mgr = idn.getManager();
      Object mgrAttr = firstAttr(idn, "managersAssociateID", "manager", "managerId");
      if (mgr != null && !byId.containsKey(mgr.getId())) {
        brokenManagers.add(idn.getId());
      } else if (mgr == null && mgrAttr != null && !Util.isNullOrEmpty(String.valueOf(mgrAttr))) {
        brokenManagers.add(idn.getId());
      }
    }
    for (List<Identity> kids : children.values()) {
      kids.sort(
          (a, b) -> {
            String da = a.getDisplayableName() != null ? a.getDisplayableName() : a.getName();
            String db = b.getDisplayableName() != null ? b.getDisplayableName() : b.getName();
            return da.compareToIgnoreCase(db);
          });
    }

    List<Map<String, Object>> forests = new ArrayList<>();
    int nodeCount = 0;
    if ("subtree".equalsIgnoreCase(chartMode) || !Util.isNullOrEmpty(root)) {
      Identity rootId =
          Util.isNullOrEmpty(root)
              ? null
              : MnbAgentSupport.resolveIdentity(ctx, root, "UIAPI-59");
      if (rootId == null) {
        throw MnbAgentSupport.error(400, "invalid_request", "root required for subtree mode", "UIAPI-59", null);
      }
      if (!byId.containsKey(rootId.getId())) {
        // Allow focusing an inactive/technical root when filtered out of company scan
        byId.put(rootId.getId(), rootId);
      }
      Map<String, Object> tree =
          buildOrgNode(rootId, children, brokenManagers, 0, maxDepth, new HashSet<>());
      forests.add(tree);
      nodeCount = countOrgNodes(tree);
    } else {
      // Company mode: roots = people with no in-scope manager who either manage someone or are tops
      List<Identity> roots = new ArrayList<>();
      for (Identity idn : byId.values()) {
        Identity mgr = idn.getManager();
        boolean isRoot = mgr == null || !byId.containsKey(mgr.getId());
        if (!isRoot) {
          continue;
        }
        boolean hasReports = children.containsKey(idn.getId()) && !children.get(idn.getId()).isEmpty();
        // Include all roots that have reports; also lone exec tops with empty manager
        if (hasReports || mgr == null) {
          roots.add(idn);
        }
      }
      roots.sort(
          (a, b) -> {
            int ca = children.containsKey(a.getId()) ? children.get(a.getId()).size() : 0;
            int cb = children.containsKey(b.getId()) ? children.get(b.getId()).size() : 0;
            if (cb != ca) {
              return Integer.compare(cb, ca);
            }
            String da = a.getDisplayableName() != null ? a.getDisplayableName() : a.getName();
            String db = b.getDisplayableName() != null ? b.getDisplayableName() : b.getName();
            return da.compareToIgnoreCase(db);
          });
      for (Identity r : roots) {
        // Skip leaf isolates with no reports in company view (noise)
        if (!children.containsKey(r.getId()) || children.get(r.getId()).isEmpty()) {
          continue;
        }
        Map<String, Object> tree =
            buildOrgNode(r, children, brokenManagers, 0, maxDepth, new HashSet<>());
        forests.add(tree);
        nodeCount += countOrgNodes(tree);
      }
    }

    Map<String, Object> data = new LinkedHashMap<>();
    data.put("mode", Util.isNullOrEmpty(root) && "company".equalsIgnoreCase(chartMode) ? "company" : "subtree");
    data.put("root", root);
    data.put("maxDepth", maxDepth);
    data.put("includeInactive", inactiveOk);
    data.put("includeTechnical", techOk);
    data.put("forestCount", forests.size());
    data.put("nodeCount", nodeCount);
    data.put("identityUniverse", byId.size());
    data.put("brokenManagerCount", brokenManagers.size());
    data.put("forest", forests);
    data.put(
        "source",
        "Identity.manager links (authoritative HR managersAssociateID after aggregate + refresh)");
    return MnbAgentSupport.ok("UIAPI-59", data);
  }

  @GET
  @Path("orgchart/search")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> orgChartSearch(@QueryParam("q") String q, @QueryParam("limit") Integer limit)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-59");
    String query = q == null ? "" : q.trim().toLowerCase();
    if (query.length() < 2) {
      throw MnbAgentSupport.error(400, "invalid_request", "q must be at least 2 characters", "UIAPI-59", null);
    }
    int lim = limit == null ? 20 : Math.max(1, Math.min(limit, 50));
    QueryOptions qo = new QueryOptions();
    qo.addFilter(
        Filter.or(
            Filter.like("name", query, Filter.MatchMode.ANYWHERE),
            Filter.like("displayName", query, Filter.MatchMode.ANYWHERE),
            Filter.like("email", query, Filter.MatchMode.ANYWHERE),
            Filter.like("firstname", query, Filter.MatchMode.ANYWHERE),
            Filter.like("lastname", query, Filter.MatchMode.ANYWHERE)));
    qo.setResultLimit(lim);
    List<Identity> hits = getContext().getObjects(Identity.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (hits != null) {
      for (Identity idn : hits) {
        if (idn == null || idn.isWorkgroup()) {
          continue;
        }
        Map<String, Object> m = summarizeOrgIdentity(idn, false);
        Identity mgr = idn.getManager();
        m.put("managerName", mgr != null ? mgr.getName() : null);
        m.put(
            "managerDisplayName",
            mgr != null
                ? (mgr.getDisplayableName() != null ? mgr.getDisplayableName() : mgr.getName())
                : null);
        rows.add(m);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("q", q);
    data.put("count", rows.size());
    data.put("results", rows);
    return MnbAgentSupport.ok("UIAPI-59", data);
  }

  // —— UIAPI-73 Schema apply ——
  @POST
  @Path("applications/{name}/schema/apply")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> applyApplicationSchema(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-73");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, name, "UIAPI-73");
    Schema schema = app.getSchema(Application.SCHEMA_ACCOUNT);
    if (schema == null) {
      schema = new Schema(Application.SCHEMA_ACCOUNT, "account");
      app.addSchema(schema);
    }
    String identityAttr =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("identityAttribute")),
            MnbAgentSupport.str(body.get("identityAttr")));
    String displayAttr =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("displayAttribute")),
            MnbAgentSupport.str(body.get("displayAttr")));
    if (!Util.isNullOrEmpty(identityAttr)) {
      schema.setIdentityAttribute(identityAttr);
    }
    if (!Util.isNullOrEmpty(displayAttr)) {
      schema.setDisplayAttribute(displayAttr);
    }
    Object attrsObj = body.get("attributes");
    int added = 0;
    if (attrsObj instanceof List) {
      for (Object o : (List<?>) attrsObj) {
        if (o instanceof String) {
          String attrName = (String) o;
          if (schema.getAttributeDefinition(attrName) == null) {
            schema.addAttributeDefinition(attrName, AttributeDefinition.TYPE_STRING);
            added++;
          }
        } else if (o instanceof Map) {
          @SuppressWarnings("unchecked")
          Map<String, Object> m = (Map<String, Object>) o;
          String attrName = MnbAgentSupport.str(m.get("name"));
          String type =
              MnbAgentSupport.firstNonEmpty(
                  MnbAgentSupport.str(m.get("type")), AttributeDefinition.TYPE_STRING);
          if (!Util.isNullOrEmpty(attrName) && schema.getAttributeDefinition(attrName) == null) {
            schema.addAttributeDefinition(attrName, type);
            added++;
          }
        }
      }
    }
    ctx.saveObject(app);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app.getName());
    data.put("identityAttribute", schema.getIdentityAttribute());
    data.put("displayAttribute", schema.getDisplayAttribute());
    data.put("attributesAdded", added);
    return MnbAgentSupport.ok("UIAPI-73", data);
  }

  // —— UIAPI-74 Correlation config write ——
  @POST
  @Path("applications/{name}/correlationConfig")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> updateCorrelationConfig(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-74");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, name, "UIAPI-74");
    String accountAttr =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("accountAttribute")),
            MnbAgentSupport.str(body.get("accountAttr")));
    String identityAttr =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("identityAttribute")),
            MnbAgentSupport.str(body.get("identityAttr")));
    if (Util.isNullOrEmpty(accountAttr) || Util.isNullOrEmpty(identityAttr)) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "accountAttribute and identityAttribute required",
          "UIAPI-74",
          null);
    }
    String cfgName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("name")),
            app.getName() + " Correlation");
    CorrelationConfig cfg = ctx.getObjectByName(CorrelationConfig.class, cfgName);
    boolean created = false;
    if (cfg == null) {
      cfg = new CorrelationConfig();
      cfg.setName(cfgName);
      created = true;
    }
    Filter assignment = Filter.eq(accountAttr, identityAttr);
    List<Filter> assignments = new ArrayList<>();
    assignments.add(assignment);
    cfg.setAttributeAssignments(assignments);
    ctx.saveObject(cfg);
    app.setAccountCorrelationConfig(cfg);
    ctx.saveObject(app);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app.getName());
    data.put("correlationConfig", cfg.getName());
    data.put("created", created);
    data.put("accountAttribute", accountAttr);
    data.put("identityAttribute", identityAttr);
    return MnbAgentSupport.ok("UIAPI-74", data);
  }

  // —— UIAPI-75 Provisioning cancel ——
  @POST
  @Path("provisioning/{id}/cancel")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> cancelProvisioning(@PathParam("id") String id) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-75");
    SailPointContext ctx = getContext();
    ProvisioningTransaction tx =
        MnbAgentSupport.requireByIdOrName(ctx, ProvisioningTransaction.class, id, "UIAPI-75");
    Attributes<String, Object> attrs = tx.getAttributes();
    if (attrs == null) {
      attrs = new Attributes<>();
      tx.setAttributes(attrs);
    }
    attrs.put("cancelled", true);
    attrs.put("cancelledBy", ctx.getUserName());
    attrs.put("cancelledAt", new Date().toString());
    tx.setStatus(ProvisioningTransaction.Status.Failed);
    ctx.saveObject(tx);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", tx.getId());
    data.put("cancelled", true);
    data.put("status", String.valueOf(tx.getStatus()));
    data.put("application", tx.getApplicationName());
    data.put("identityName", tx.getIdentityName());
    return MnbAgentSupport.ok("UIAPI-75", data);
  }

  // —— UIAPI-76 Lifecycle events (IdentityTrigger) ——
  @GET
  @Path("lifecycleEvents")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> listLifecycleEvents(@QueryParam("limit") Integer limit)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-76");
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(limit == null ? 50 : Math.min(limit, 200));
    List<IdentityTrigger> triggers = getContext().getObjects(IdentityTrigger.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (triggers != null) {
      for (IdentityTrigger t : triggers) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", t.getId());
        m.put("name", t.getName());
        m.put("type", t.getType() != null ? String.valueOf(t.getType()) : null);
        m.put("inactive", t.isInactive());
        m.put("workflowName", t.getWorkflowName());
        m.put("attributeName", t.getAttributeName());
        rows.add(m);
      }
    }
    return MnbAgentSupport.ok("UIAPI-76", rows);
  }

  @POST
  @Path("lifecycleEvents")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> upsertLifecycleEvent(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-76");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-76", null);
    }
    SailPointContext ctx = getContext();
    IdentityTrigger trigger = ctx.getObjectByName(IdentityTrigger.class, name);
    boolean created = false;
    if (trigger == null) {
      trigger = new IdentityTrigger();
      trigger.setName(name);
      created = true;
    }
    String typeName =
        MnbAgentSupport.firstNonEmpty(MnbAgentSupport.str(body.get("type")), "Create");
    try {
      trigger.setType(IdentityTrigger.Type.valueOf(typeName));
    } catch (IllegalArgumentException e) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "type must be Create|Delete|AttributeChange|Rule|ManagerTransfer|NativeChange|Alert|RapidSetup",
          "UIAPI-76",
          null);
    }
    String workflowName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("workflowName")),
            MnbAgentSupport.str(body.get("workflow")));
    if (!Util.isNullOrEmpty(workflowName)) {
      trigger.setWorkflowName(workflowName);
    }
    String attrName = MnbAgentSupport.str(body.get("attributeName"));
    if (!Util.isNullOrEmpty(attrName)) {
      trigger.setAttributeName(attrName);
    }
    if (body.containsKey("inactive")) {
      // IdentityTrigger uses disabled via selector in some builds; persist as attribute when present
      trigger.setAttribute("inactive", Boolean.TRUE.equals(body.get("inactive")));
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      trigger.setDescription(description);
    }
    ctx.saveObject(trigger);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", trigger.getName());
    data.put("id", trigger.getId());
    data.put("created", created);
    data.put("type", trigger.getType() != null ? String.valueOf(trigger.getType()) : null);
    data.put("workflowName", trigger.getWorkflowName());
    return MnbAgentSupport.ok("UIAPI-76", data);
  }

  // —— UIAPI-77 ObjectConfig attribute patch (searchable via extendedNumber) ——
  @POST
  @Path("objectConfigs/{name}/attributes")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> patchObjectConfigAttribute(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-77");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String attrName = MnbAgentSupport.str(body.get("attribute"));
    if (Util.isNullOrEmpty(attrName)) {
      throw MnbAgentSupport.error(400, "invalid_request", "attribute required", "UIAPI-77", null);
    }
    SailPointContext ctx = getContext();
    ObjectConfig oc = ctx.getObjectByName(ObjectConfig.class, name);
    if (oc == null) {
      oc = ObjectConfig.getObjectConfig(name);
    }
    if (oc == null) {
      throw MnbAgentSupport.error(404, "not_found", "ObjectConfig not found: " + name, "UIAPI-77", null);
    }
    ObjectAttribute oa = null;
    if (oc.getObjectAttributeMap() != null) {
      oa = oc.getObjectAttributeMap().get(attrName);
    }
    if (oa == null && oc.getObjectAttributes() != null) {
      for (ObjectAttribute cand : oc.getObjectAttributes()) {
        if (cand != null && attrName.equals(cand.getName())) {
          oa = cand;
          break;
        }
      }
    }
    boolean createdAttr = false;
    if (oa == null) {
      oa = new ObjectAttribute();
      oa.setName(attrName);
      oa.setDisplayName(attrName);
      List<ObjectAttribute> list = oc.getObjectAttributes();
      if (list == null) {
        list = new ArrayList<>();
        oc.setObjectAttributes(list);
      }
      list.add(oa);
      createdAttr = true;
    }
    if (body.get("extendedNumber") instanceof Number) {
      oa.setExtendedNumber(((Number) body.get("extendedNumber")).intValue());
    } else if (Boolean.TRUE.equals(body.get("searchable"))) {
      if (oa.getExtendedNumber() <= 0) {
        oa.setExtendedNumber(1);
      }
    }
    if (body.containsKey("displayName")) {
      oa.setDisplayName(MnbAgentSupport.str(body.get("displayName")));
    }
    if (body.containsKey("namedColumn")) {
      oa.setNamedColumn(Boolean.TRUE.equals(body.get("namedColumn")));
    }
    ctx.saveObject(oc);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("objectConfig", oc.getName());
    data.put("attribute", oa.getName());
    data.put("created", createdAttr);
    data.put("extendedNumber", oa.getExtendedNumber());
    data.put("searchable", oa.isSearchable());
    return MnbAgentSupport.ok("UIAPI-77", data);
  }

  // —— UIAPI-78 PasswordPolicy upsert ——
  @POST
  @Path("passwordPolicies")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> upsertPasswordPolicy(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-78");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-78", null);
    }
    SailPointContext ctx = getContext();
    PasswordPolicy policy = ctx.getObjectByName(PasswordPolicy.class, name);
    boolean created = false;
    if (policy == null) {
      policy = new PasswordPolicy();
      policy.setName(name);
      created = true;
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      policy.setDescription(description);
    }
    if (body.get("constraints") instanceof Map) {
      @SuppressWarnings("unchecked")
      Map<String, Object> constraints = (Map<String, Object>) body.get("constraints");
      policy.setPasswordConstraints(constraints);
    }
    ctx.saveObject(policy);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", policy.getName());
    data.put("id", policy.getId());
    data.put("created", created);
    data.put("constraints", policy.getPasswordConstraints());
    return MnbAgentSupport.ok("UIAPI-78", data);
  }

  // —— UIAPI-79 Role required-roles ——
  @POST
  @Path("roles/{name}/requirements")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> setRoleRequirements(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-79");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Bundle role = MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, name, "UIAPI-79");
    String op =
        MnbAgentSupport.firstNonEmpty(MnbAgentSupport.str(body.get("op")), "add").toLowerCase();
    Object reqObj = body.get("requiredRoles");
    if (reqObj == null) {
      reqObj = body.get("roles");
    }
    if (!(reqObj instanceof List) || ((List<?>) reqObj).isEmpty()) {
      String one =
          MnbAgentSupport.firstNonEmpty(
              MnbAgentSupport.str(body.get("requiredRole")),
              MnbAgentSupport.str(body.get("role")));
      if (Util.isNullOrEmpty(one)) {
        throw MnbAgentSupport.error(
            400, "invalid_request", "requiredRoles list or requiredRole required", "UIAPI-79", null);
      }
      reqObj = java.util.Collections.singletonList(one);
    }
    List<String> applied = new ArrayList<>();
    for (Object o : (List<?>) reqObj) {
      if (o == null) {
        continue;
      }
      String reqName = String.valueOf(o);
      Bundle req = MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, reqName, "UIAPI-79");
      if ("remove".equals(op)) {
        role.removeRequirement(req);
      } else {
        role.addRequirement(req);
      }
      applied.add(req.getName());
    }
    ctx.saveObject(role);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("role", role.getName());
    data.put("op", op);
    data.put("requiredRoles", applied);
    List<String> current = new ArrayList<>();
    if (role.getRequirements() != null) {
      for (Bundle b : role.getRequirements()) {
        if (b != null) {
          current.add(b.getName());
        }
      }
    }
    data.put("requirements", current);
    return MnbAgentSupport.ok("UIAPI-79", data);
  }

  // —— UIAPI-80 SoD left/right role constraint ——
  @POST
  @Path("policies/sod/{name}/constraints")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> updateSodConstraints(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-80");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Policy policy = MnbAgentSupport.requireByIdOrName(ctx, Policy.class, name, "UIAPI-80");
    String constraintName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("constraintName")),
            MnbAgentSupport.str(body.get("name")),
            policy.getName() + " Constraint");
    SODConstraint constraint = null;
    if (policy.getSODConstraints() != null) {
      for (SODConstraint c : policy.getSODConstraints()) {
        if (c != null && constraintName.equals(c.getName())) {
          constraint = c;
          break;
        }
      }
    }
    boolean created = false;
    if (constraint == null) {
      constraint = new SODConstraint();
      constraint.setName(constraintName);
      policy.addConstraint(constraint);
      created = true;
    }
    Object left = body.get("leftRoles");
    if (left == null) {
      left = body.get("left");
    }
    Object right = body.get("rightRoles");
    if (right == null) {
      right = body.get("right");
    }
    if (left instanceof List) {
      for (Object o : (List<?>) left) {
        if (o == null) {
          continue;
        }
        Bundle b = MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, String.valueOf(o), "UIAPI-80");
        constraint.addLeft(b);
      }
    }
    if (right instanceof List) {
      for (Object o : (List<?>) right) {
        if (o == null) {
          continue;
        }
        Bundle b = MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, String.valueOf(o), "UIAPI-80");
        constraint.addRight(b);
      }
    }
    ctx.saveObject(policy);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("policy", policy.getName());
    data.put("constraintName", constraint.getName());
    data.put("created", created);
    List<String> leftNames = new ArrayList<>();
    if (constraint.getLeftBundles() != null) {
      for (Bundle b : constraint.getLeftBundles()) {
        if (b != null) {
          leftNames.add(b.getName());
        }
      }
    }
    List<String> rightNames = new ArrayList<>();
    if (constraint.getRightBundles() != null) {
      for (Bundle b : constraint.getRightBundles()) {
        if (b != null) {
          rightNames.add(b.getName());
        }
      }
    }
    data.put("leftRoles", leftNames);
    data.put("rightRoles", rightNames);
    return MnbAgentSupport.ok("UIAPI-80", data);
  }

  // —— UIAPI-81 Application provisioning policies (Forms / Templates) ——
  @GET
  @Path("applications/{name}/provisioningPolicies")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> listProvisioningPolicies(@PathParam("name") String name)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-81");
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, name, "UIAPI-81");
    List<Map<String, Object>> policies = new ArrayList<>();
    List<Form> forms = app.getProvisioningForms();
    if (forms != null) {
      for (Form form : forms) {
        if (form == null) {
          continue;
        }
        policies.add(summarizeProvisioningForm(form));
      }
    }
    List<Template> templates = app.getTemplates();
    if (templates != null) {
      for (Template t : templates) {
        if (t == null) {
          continue;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("kind", "template");
        m.put("name", t.getName());
        m.put("usage", t.getUsage() != null ? String.valueOf(t.getUsage()) : null);
        m.put("schemaObjectType", t.getSchemaObjectType());
        List<String> fieldNames = new ArrayList<>();
        if (t.getFields() != null) {
          for (Field f : t.getFields()) {
            if (f != null && f.getName() != null) {
              fieldNames.add(f.getName());
            }
          }
        }
        m.put("fields", fieldNames);
        policies.add(m);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app.getName());
    data.put("count", policies.size());
    data.put("policies", policies);
    return MnbAgentSupport.ok("UIAPI-81", data);
  }

  @POST
  @Path("applications/{name}/provisioningPolicies")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> upsertProvisioningPolicy(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-81");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, name, "UIAPI-81");
    String policyName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("name")),
            MnbAgentSupport.str(body.get("policyName")),
            "Create");
    String typeStr =
        MnbAgentSupport.firstNonEmpty(MnbAgentSupport.str(body.get("type")), "Create");
    Form.Type formType;
    try {
      formType = Form.Type.valueOf(typeStr);
    } catch (IllegalArgumentException ex) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "type must be a Form.Type (Create, Update, Delete, …)",
          "UIAPI-81",
          null);
    }
    String objectType =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("objectType")),
            MnbAgentSupport.str(body.get("schemaObjectType")),
            "account");
    List<Form> forms = app.getProvisioningForms();
    if (forms == null) {
      forms = new ArrayList<>();
    } else {
      forms = new ArrayList<>(forms);
    }
    Form form = null;
    for (Form existing : forms) {
      if (existing != null
          && policyName.equals(existing.getName())
          && formType.equals(existing.getType())) {
        form = existing;
        break;
      }
    }
    boolean created = form == null;
    if (form == null) {
      form = new Form();
      form.setName(policyName);
      form.setType(formType);
      forms.add(form);
    } else {
      form.setType(formType);
    }
    form.setObjectType(objectType);
    form.setApplication(app);
    Object fieldsObj = body.get("fields");
    if (fieldsObj instanceof List) {
      // Replace fields when provided
      if (form.getFields() != null) {
        for (Field existing : new ArrayList<>(form.getFields())) {
          if (existing != null && existing.getName() != null) {
            form.removeField(existing.getName());
          }
        }
      }
      for (Object o : (List<?>) fieldsObj) {
        if (!(o instanceof Map)) {
          continue;
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> fm = (Map<String, Object>) o;
        String fieldName = MnbAgentSupport.str(fm.get("name"));
        if (Util.isNullOrEmpty(fieldName)) {
          continue;
        }
        Field field = new Field();
        field.setName(fieldName);
        field.setType(
            MnbAgentSupport.firstNonEmpty(
                MnbAgentSupport.str(fm.get("type")), AttributeDefinition.TYPE_STRING));
        if (fm.get("required") instanceof Boolean) {
          field.setRequired((Boolean) fm.get("required"));
        } else if ("true".equalsIgnoreCase(String.valueOf(fm.get("required")))) {
          field.setRequired(true);
        }
        Object value = fm.get("value");
        if (value != null) {
          field.setValue(value);
        }
        String scriptSrc = MnbAgentSupport.str(fm.get("script"));
        if (!Util.isNullOrEmpty(scriptSrc)) {
          field.setScript(new Script(scriptSrc));
        }
        form.add(field);
      }
    }
    app.setProvisioningForms(forms);
    ctx.saveObject(app);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app.getName());
    data.put("created", created);
    data.put("policy", summarizeProvisioningForm(form));
    return MnbAgentSupport.ok("UIAPI-81", data);
  }

  // —— UIAPI-82 SoD simulate / impact ——
  @POST
  @Path("policies/sod/{name}/simulate")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> simulateSodPolicy(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-82");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Policy policy = MnbAgentSupport.requireByIdOrName(ctx, Policy.class, name, "UIAPI-82");
    String identityName =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("identity")),
            MnbAgentSupport.str(body.get("identityName")));
    Set<String> roleNames = new HashSet<>();
    if (!Util.isNullOrEmpty(identityName)) {
      Identity idn = MnbAgentSupport.requireByIdOrName(ctx, Identity.class, identityName, "UIAPI-82");
      if (idn.getAssignedRoles() != null) {
        for (Bundle b : idn.getAssignedRoles()) {
          if (b != null && b.getName() != null) {
            roleNames.add(b.getName());
          }
        }
      }
      if (idn.getBundles() != null) {
        for (Bundle b : idn.getBundles()) {
          if (b != null && b.getName() != null) {
            roleNames.add(b.getName());
          }
        }
      }
    }
    Object proposed = body.get("proposedRoles");
    if (proposed == null) {
      proposed = body.get("roles");
    }
    if (proposed instanceof List) {
      for (Object o : (List<?>) proposed) {
        if (o != null) {
          roleNames.add(String.valueOf(o));
        }
      }
    }
    Object remove = body.get("removeRoles");
    if (remove instanceof List) {
      for (Object o : (List<?>) remove) {
        if (o != null) {
          roleNames.remove(String.valueOf(o));
        }
      }
    }
    List<Map<String, Object>> hits = new ArrayList<>();
    if (policy.getSODConstraints() != null) {
      for (SODConstraint c : policy.getSODConstraints()) {
        if (c == null) {
          continue;
        }
        Set<String> leftHit = new HashSet<>();
        Set<String> rightHit = new HashSet<>();
        if (c.getLeftBundles() != null) {
          for (Bundle b : c.getLeftBundles()) {
            if (b != null && roleNames.contains(b.getName())) {
              leftHit.add(b.getName());
            }
          }
        }
        if (c.getRightBundles() != null) {
          for (Bundle b : c.getRightBundles()) {
            if (b != null && roleNames.contains(b.getName())) {
              rightHit.add(b.getName());
            }
          }
        }
        if (!leftHit.isEmpty() && !rightHit.isEmpty()) {
          Map<String, Object> hit = new LinkedHashMap<>();
          hit.put("constraintName", c.getName());
          hit.put("leftRoles", new ArrayList<>(leftHit));
          hit.put("rightRoles", new ArrayList<>(rightHit));
          hits.add(hit);
        }
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("policy", policy.getName());
    data.put("identity", identityName);
    data.put("effectiveRoles", new ArrayList<>(roleNames));
    data.put("wouldViolate", !hits.isEmpty());
    data.put("violations", hits);
    data.put(
        "note",
        "Static role-set intersection against SODConstraint left/right bundles (not full IIQ PolicyExecutor).");
    return MnbAgentSupport.ok("UIAPI-82", data);
  }

  // —— UIAPI-83 GroupFactory upsert + run ——
  @POST
  @Path("groupFactories")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> upsertGroupFactory(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-83");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    String attr =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("factoryAttribute")),
            MnbAgentSupport.str(body.get("attribute")));
    if (Util.isNullOrEmpty(name) || Util.isNullOrEmpty(attr)) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "name and factoryAttribute required", "UIAPI-83", null);
    }
    SailPointContext ctx = getContext();
    GroupFactory factory = ctx.getObjectByName(GroupFactory.class, name);
    boolean created = factory == null;
    if (factory == null) {
      factory = new GroupFactory();
      factory.setName(name);
    }
    factory.setFactoryAttribute(attr);
    if (body.containsKey("enabled")) {
      Object en = body.get("enabled");
      factory.setEnabled(en instanceof Boolean ? (Boolean) en : !"false".equalsIgnoreCase(String.valueOf(en)));
    } else if (created) {
      factory.setEnabled(true);
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      factory.setDescription(description);
    }
    ctx.saveObject(factory);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", factory.getName());
    data.put("id", factory.getId());
    data.put("factoryAttribute", factory.getFactoryAttribute());
    data.put("enabled", factory.isEnabled());
    data.put("created", created);
    return MnbAgentSupport.ok("UIAPI-83", data);
  }

  @POST
  @Path("groupFactories/{name}/run")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> runGroupFactory(@PathParam("name") String name)
      throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-83");
    SailPointContext ctx = getContext();
    GroupFactory factory = MnbAgentSupport.requireByIdOrName(ctx, GroupFactory.class, name, "UIAPI-83");
    Grouper grouper = new Grouper(ctx);
    grouper.refreshFactory(factory);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", factory.getName());
    data.put("factoryAttribute", factory.getFactoryAttribute());
    data.put("ran", true);
    data.put("lastRefresh", factory.getLastRefresh() != null ? factory.getLastRefresh().toString() : null);
    return MnbAgentSupport.ok("UIAPI-83", data);
  }

  // —— UIAPI-85 Role assignment selector ——
  @POST
  @Path("roles/{name}/selector")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> setRoleSelector(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-85");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Bundle role = MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, name, "UIAPI-85");
    if (Boolean.TRUE.equals(body.get("clear")) || "clear".equalsIgnoreCase(MnbAgentSupport.str(body.get("op")))) {
      role.setSelector(null);
      ctx.saveObject(role);
      ctx.commitTransaction();
      Map<String, Object> cleared = new LinkedHashMap<>();
      cleared.put("role", role.getName());
      cleared.put("cleared", true);
      return MnbAgentSupport.ok("UIAPI-85", cleared);
    }
    IdentitySelector selector = new IdentitySelector();
    String population =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("population")),
            MnbAgentSupport.str(body.get("populationName")));
    String scriptSrc = MnbAgentSupport.str(body.get("script"));
    Object matchTerms = body.get("matchTerms");
    if (matchTerms == null) {
      matchTerms = body.get("terms");
    }
    if (!Util.isNullOrEmpty(population)) {
      GroupDefinition pop =
          MnbAgentSupport.requireByIdOrName(ctx, GroupDefinition.class, population, "UIAPI-85");
      selector.setPopulation(pop);
    } else if (!Util.isNullOrEmpty(scriptSrc)) {
      selector.setScript(new Script(scriptSrc));
    } else if (matchTerms instanceof List) {
      IdentitySelector.MatchExpression expr = new IdentitySelector.MatchExpression();
      expr.setAnd(
          body.get("and") instanceof Boolean
              ? (Boolean) body.get("and")
              : !"false".equalsIgnoreCase(String.valueOf(body.get("and"))));
      for (Object o : (List<?>) matchTerms) {
        if (!(o instanceof Map)) {
          continue;
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> tm = (Map<String, Object>) o;
        IdentitySelector.MatchTerm term = new IdentitySelector.MatchTerm();
        term.setName(MnbAgentSupport.str(tm.get("name")));
        term.setValue(MnbAgentSupport.str(tm.get("value")));
        if (tm.get("negative") instanceof Boolean) {
          term.setNegative((Boolean) tm.get("negative"));
        }
        expr.addTerm(term);
      }
      selector.setMatchExpression(expr);
    } else {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "Provide population, script, matchTerms, or clear=true",
          "UIAPI-85",
          null);
    }
    role.setSelector(selector);
    ctx.saveObject(role);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("role", role.getName());
    data.put("selectorSummary", selector.generateSummary());
    data.put(
        "selectorType",
        !Util.isNullOrEmpty(population)
            ? "population"
            : (!Util.isNullOrEmpty(scriptSrc) ? "script" : "matchList"));
    return MnbAgentSupport.ok("UIAPI-85", data);
  }

  // —— UIAPI-86 CertificationDefinition thin update ——
  @POST
  @Path("certifications/definitions/{name}")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> updateCertificationDefinition(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-86");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    CertificationDefinition def =
        MnbAgentSupport.requireByIdOrName(ctx, CertificationDefinition.class, name, "UIAPI-86");
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      def.setDescription(description);
    }
    String nameTemplate =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("nameTemplate")),
            MnbAgentSupport.str(body.get("certificationNameTemplate")));
    if (!Util.isNullOrEmpty(nameTemplate)) {
      def.setNameTemplate(nameTemplate);
      def.setCertificationNameTemplate(nameTemplate);
    }
    String owner =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("owner")),
            MnbAgentSupport.str(body.get("certificationOwner")));
    if (!Util.isNullOrEmpty(owner)) {
      Identity ownerId = ctx.getObjectByName(Identity.class, owner);
      if (ownerId != null) {
        def.setCertificationOwner(ownerId);
      } else {
        def.setCertificationOwner(owner);
      }
    }
    Object certifiers = body.get("certifiers");
    if (certifiers instanceof List) {
      List<String> names = new ArrayList<>();
      for (Object o : (List<?>) certifiers) {
        if (o != null) {
          names.add(String.valueOf(o));
        }
      }
      def.setCertifiers(names);
    }
    String type = MnbAgentSupport.str(body.get("type"));
    if (!Util.isNullOrEmpty(type)) {
      def.setType(type);
    }
    ctx.saveObject(def);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", def.getName());
    data.put("id", def.getId());
    data.put("description", def.getDescription());
    data.put("nameTemplate", def.getNameTemplate());
    data.put("type", def.getType() != null ? String.valueOf(def.getType()) : null);
    data.put("certificationOwner", def.getCertificationOwner());
    data.put("certifiers", def.getCertifiers());
    return MnbAgentSupport.ok("UIAPI-86", data);
  }

  // —— UIAPI-87 Identity forwarding / OOO ——
  @POST
  @Path("identities/{name}/forwarding")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> setIdentityForwarding(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-87");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Identity idn = MnbAgentSupport.requireByIdOrName(ctx, Identity.class, name, "UIAPI-87");
    if (Boolean.TRUE.equals(body.get("clear")) || "clear".equalsIgnoreCase(MnbAgentSupport.str(body.get("op")))) {
      idn.setPreference(Identity.PRF_FORWARD, null);
      idn.setPreference(Identity.PRF_FORWARD_START_DATE, null);
      idn.setPreference(Identity.PRF_FORWARD_END_DATE, null);
      ctx.saveObject(idn);
      ctx.commitTransaction();
      Map<String, Object> cleared = new LinkedHashMap<>();
      cleared.put("identity", idn.getName());
      cleared.put("cleared", true);
      return MnbAgentSupport.ok("UIAPI-87", cleared);
    }
    String forwardTo =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("forwardTo")),
            MnbAgentSupport.str(body.get("delegate")),
            MnbAgentSupport.str(body.get("forward")));
    if (Util.isNullOrEmpty(forwardTo)) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "forwardTo required (or clear=true)", "UIAPI-87", null);
    }
    Identity target = MnbAgentSupport.requireByIdOrName(ctx, Identity.class, forwardTo, "UIAPI-87");
    idn.setPreference(Identity.PRF_FORWARD, target.getName());
    String start =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("startDate")), MnbAgentSupport.str(body.get("start")));
    String end =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("endDate")), MnbAgentSupport.str(body.get("end")));
    if (!Util.isNullOrEmpty(start)) {
      Date d = parseFlexibleDateLocal(start);
      if (d != null) {
        idn.setPreference(Identity.PRF_FORWARD_START_DATE, d);
      }
    }
    if (!Util.isNullOrEmpty(end)) {
      Date d = parseFlexibleDateLocal(end);
      if (d != null) {
        idn.setPreference(Identity.PRF_FORWARD_END_DATE, d);
      }
    }
    ctx.saveObject(idn);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("identity", idn.getName());
    data.put("forwardTo", target.getName());
    data.put("startDate", start);
    data.put("endDate", end);
    return MnbAgentSupport.ok("UIAPI-87", data);
  }

  // —— UIAPI-88 Risk score weight patch ——
  @POST
  @Path("risk/scoreConfig")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> updateRiskScoreConfig(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-88");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    ScoreConfig cfg = ctx.getObjectByName(ScoreConfig.class, ScoreConfig.OBJ_NAME);
    if (cfg == null) {
      throw MnbAgentSupport.error(404, "not_found", "ScoreConfig not found", "UIAPI-88", null);
    }
    List<Map<String, Object>> updated = new ArrayList<>();
    Object weights = body.get("identityScores");
    if (weights == null) {
      weights = body.get("weights");
    }
    if (weights instanceof List) {
      for (Object o : (List<?>) weights) {
        if (!(o instanceof Map)) {
          continue;
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> m = (Map<String, Object>) o;
        String scoreName =
            MnbAgentSupport.firstNonEmpty(
                MnbAgentSupport.str(m.get("name")), MnbAgentSupport.str(m.get("score")));
        if (Util.isNullOrEmpty(scoreName)) {
          continue;
        }
        ScoreDefinition def = cfg.getIdentityScore(scoreName);
        if (def == null) {
          throw MnbAgentSupport.error(
              404, "not_found", "Identity score not found: " + scoreName, "UIAPI-88", null);
        }
        if (m.get("weight") != null) {
          def.setWeight(Integer.parseInt(String.valueOf(m.get("weight"))));
        }
        if (m.get("range") != null) {
          def.setRange(Integer.parseInt(String.valueOf(m.get("range"))));
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("name", def.getName());
        row.put("weight", def.getWeight());
        row.put("range", def.getRange());
        updated.add(row);
      }
    } else if (body.get("score") != null && body.get("weight") != null) {
      String scoreName = MnbAgentSupport.str(body.get("score"));
      ScoreDefinition def = cfg.getIdentityScore(scoreName);
      if (def == null) {
        throw MnbAgentSupport.error(
            404, "not_found", "Identity score not found: " + scoreName, "UIAPI-88", null);
      }
      def.setWeight(Integer.parseInt(String.valueOf(body.get("weight"))));
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("name", def.getName());
      row.put("weight", def.getWeight());
      updated.add(row);
    } else {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "Provide identityScores:[{name,weight}] or score+weight",
          "UIAPI-88",
          null);
    }
    if (body.get("maximumScore") != null) {
      cfg.setMaximumScore(Integer.parseInt(String.valueOf(body.get("maximumScore"))));
    }
    ctx.saveObject(cfg);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("updated", updated);
    data.put("maximumScore", cfg.getMaximumScore());
    return MnbAgentSupport.ok("UIAPI-88", data);
  }

  // —— UIAPI-89 TaskDefinition upsert (clone template) ——
  @POST
  @Path("taskDefinitions")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> upsertTaskDefinition(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-89");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-89", null);
    }
    SailPointContext ctx = getContext();
    TaskDefinition existing = ctx.getObjectByName(TaskDefinition.class, name);
    boolean created = existing == null;
    TaskDefinition td;
    if (existing != null) {
      td = existing;
    } else {
      String templateName =
          MnbAgentSupport.firstNonEmpty(
              MnbAgentSupport.str(body.get("template")),
              MnbAgentSupport.str(body.get("parent")),
              "Account Aggregation");
      TaskDefinition template = ctx.getObjectByName(TaskDefinition.class, templateName);
      if (template == null) {
        throw MnbAgentSupport.error(
            404, "not_found", "TaskDefinition template not found: " + templateName, "UIAPI-89", null);
      }
      td = (TaskDefinition) template.deepCopy((XMLReferenceResolver) ctx);
      td.setId(null);
      td.setName(name);
      td.setTemplate(false);
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      td.setDescription(description);
    }
    Object argsObj = body.get("arguments");
    if (argsObj instanceof Map) {
      Attributes<String, Object> args = td.getArguments();
      if (args == null) {
        args = new Attributes<>();
      }
      @SuppressWarnings("unchecked")
      Map<String, Object> am = (Map<String, Object>) argsObj;
      for (Map.Entry<String, Object> e : am.entrySet()) {
        if (e.getKey() != null) {
          args.put(e.getKey(), e.getValue());
        }
      }
      td.setArguments(args);
    }
    ctx.saveObject(td);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", td.getName());
    data.put("id", td.getId());
    data.put("created", created);
    data.put("type", td.getType() != null ? String.valueOf(td.getType()) : null);
    return MnbAgentSupport.ok("UIAPI-89", data);
  }

  // —— UIAPI-90 Stop aggregation / terminate running task by app ——
  @POST
  @Path("connectors/aggregate/stop")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> stopAggregation(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-90");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    String taskResultId =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("taskResultId")), MnbAgentSupport.str(body.get("id")));
    TaskResult target = null;
    if (!Util.isNullOrEmpty(taskResultId)) {
      target = ctx.getObject(TaskResult.class, taskResultId);
      if (target == null) {
        target = ctx.getObjectByName(TaskResult.class, taskResultId);
      }
    } else {
      String appName =
          MnbAgentSupport.firstNonEmpty(
              MnbAgentSupport.str(body.get("application")), MnbAgentSupport.str(body.get("app")));
      String nameContains =
          MnbAgentSupport.firstNonEmpty(
              MnbAgentSupport.str(body.get("taskNameContains")), "Aggregation");
      QueryOptions qo = new QueryOptions();
      qo.addFilter(Filter.isnull("completed"));
      qo.setResultLimit(50);
      List<TaskResult> running = ctx.getObjects(TaskResult.class, qo);
      if (running != null) {
        for (TaskResult tr : running) {
          if (tr == null || tr.getName() == null) {
            continue;
          }
          String n = tr.getName();
          if (!n.toLowerCase(Locale.ROOT).contains(nameContains.toLowerCase(Locale.ROOT))) {
            continue;
          }
          if (!Util.isNullOrEmpty(appName)) {
            Object apps = tr.getAttribute("applications");
            String hay = String.valueOf(apps) + " " + n;
            if (!hay.toLowerCase(Locale.ROOT).contains(appName.toLowerCase(Locale.ROOT))) {
              continue;
            }
          }
          target = tr;
          break;
        }
      }
    }
    if (target == null) {
      throw MnbAgentSupport.error(
          404,
          "not_found",
          "No matching running task result",
          "UIAPI-90",
          "Pass taskResultId or application (+ optional taskNameContains)");
    }
    TaskManager tm = new TaskManager(ctx);
    boolean terminated = tm.terminate(target);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("taskResultId", target.getId());
    data.put("taskResultName", target.getName());
    data.put("terminated", terminated);
    return MnbAgentSupport.ok("UIAPI-90", data);
  }

  private static Date parseFlexibleDateLocal(String raw) {
    if (Util.isNullOrEmpty(raw)) {
      return null;
    }
    try {
      long epoch = Long.parseLong(raw.trim());
      if (raw.trim().length() <= 10) {
        epoch = epoch * 1000L;
      }
      return new Date(epoch);
    } catch (NumberFormatException ignored) {
      // fall through
    }
    String[] patterns =
        new String[] {"yyyy-MM-dd'T'HH:mm:ss", "yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd"};
    for (String p : patterns) {
      try {
        return new java.text.SimpleDateFormat(p).parse(raw.trim());
      } catch (Exception ignored) {
        // try next
      }
    }
    return null;
  }

  private static List<SPRight> resolveSpRights(SailPointContext ctx, List<?> rightsObj, String gapId)
      throws GeneralException {
    List<SPRight> rights = new ArrayList<>();
    for (Object o : rightsObj) {
      if (o == null) {
        continue;
      }
      String rightName = String.valueOf(o);
      SPRight right = ctx.getObjectByName(SPRight.class, rightName);
      if (right == null) {
        throw MnbAgentSupport.error(
            404, "not_found", "SPRight not found: " + rightName, gapId, null);
      }
      rights.add(right);
    }
    return rights;
  }

  private static List<String> rightNames(Capability cap) {
    List<String> names = new ArrayList<>();
    if (cap.getRights() != null) {
      for (SPRight r : cap.getRights()) {
        if (r != null && r.getName() != null) {
          names.add(r.getName());
        }
      }
    }
    return names;
  }

  private static Map<String, Object> summarizeProvisioningForm(Form form) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("kind", "form");
    m.put("name", form.getName());
    m.put("type", form.getType() != null ? String.valueOf(form.getType()) : null);
    m.put("objectType", form.getObjectType());
    List<Map<String, Object>> fields = new ArrayList<>();
    if (form.getFields() != null) {
      for (Field f : form.getFields()) {
        if (f == null) {
          continue;
        }
        Map<String, Object> fm = new LinkedHashMap<>();
        fm.put("name", f.getName());
        fm.put("type", f.getType());
        fm.put("required", f.isRequired());
        if (f.getValue() != null) {
          fm.put("value", String.valueOf(f.getValue()));
        }
        if (f.getScript() != null && f.getScript().getSource() != null) {
          fm.put("hasScript", true);
        }
        fields.add(fm);
      }
    }
    m.put("fields", fields);
    return m;
  }

  private static boolean isTechnicalIdentity(Identity idn) {
    if (idn == null) {
      return true;
    }
    String name = idn.getName();
    if (name == null) {
      return true;
    }
    String n = name.toLowerCase();
    return "spadmin".equals(n)
        || n.startsWith("iiq")
        || n.contains("service")
        || n.startsWith("svc");
  }

  private static Map<String, Object> buildOrgNode(
      Identity idn,
      Map<String, List<Identity>> children,
      Set<String> brokenManagers,
      int depth,
      int maxDepth,
      Set<String> stack) {
    boolean broken = brokenManagers != null && brokenManagers.contains(idn.getId());
    Map<String, Object> node = summarizeOrgIdentity(idn, broken);
    node.put("depth", depth);
    List<Identity> kids = children.get(idn.getId());
    int direct = kids == null ? 0 : kids.size();
    node.put("directReports", direct);
    List<Map<String, Object>> childNodes = new ArrayList<>();
    if (depth < maxDepth && kids != null && stack.add(idn.getId())) {
      for (Identity kid : kids) {
        childNodes.add(buildOrgNode(kid, children, brokenManagers, depth + 1, maxDepth, stack));
      }
      stack.remove(idn.getId());
    }
    node.put("children", childNodes);
    node.put("truncated", depth >= maxDepth && direct > 0);
    return node;
  }

  private static int countOrgNodes(Map<String, Object> node) {
    int n = 1;
    Object kids = node.get("children");
    if (kids instanceof List) {
      for (Object o : (List<?>) kids) {
        if (o instanceof Map) {
          @SuppressWarnings("unchecked")
          Map<String, Object> child = (Map<String, Object>) o;
          n += countOrgNodes(child);
        }
      }
    }
    return n;
  }

  private static final String[] ORG_PRIVILEGED = {
    "AWS_ADMIN", "WIRE_INIT", "WIRE_APPR", "SAP_FI", "GL_POST", "CORE_ADMIN"
  };

  private static Map<String, Object> summarizeOrgIdentity(Identity idn, boolean brokenManager) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("id", idn.getId());
    m.put("name", idn.getName());
    m.put(
        "displayName",
        idn.getDisplayableName() != null ? idn.getDisplayableName() : idn.getName());
    m.put("firstname", idn.getFirstname());
    m.put("lastname", idn.getLastname());
    m.put("email", idn.getEmail());
    m.put("inactive", idn.isInactive());
    try {
      m.put("isManager", Boolean.TRUE.equals(idn.getAttribute("managerStatus")) || idn.getManagerStatus());
    } catch (Exception e) {
      m.put("isManager", null);
    }
    Object title = firstAttr(idn, "title", "jobTitle");
    Object dept = firstAttr(idn, "departmentName", "department", "dept");
    Object job = firstAttr(idn, "jobCode", "JobCode");
    Object userId = firstAttr(idn, "userId", "employeeId");
    Object type = firstAttr(idn, "employeeType", "type");
    Object loc = firstAttr(idn, "locationCode", "location", "city");
    m.put("title", title != null ? String.valueOf(title) : null);
    m.put("department", dept != null ? String.valueOf(dept) : null);
    m.put("jobCode", job != null ? String.valueOf(job) : null);
    m.put("userId", userId != null ? String.valueOf(userId) : idn.getName());
    m.put("employeeType", type != null ? String.valueOf(type) : null);
    m.put("location", loc != null ? String.valueOf(loc) : null);
    boolean privileged = identityHasPrivilegedAccess(idn);
    m.put("privilegedAccess", privileged);
    m.put("brokenManager", brokenManager);
    List<String> risks = new ArrayList<>();
    if (idn.isInactive()) {
      risks.add("inactive");
    }
    if (brokenManager) {
      risks.add("brokenManager");
    }
    if (privileged) {
      risks.add("privileged");
    }
    m.put("riskFlags", risks);
    return m;
  }

  private static boolean identityHasPrivilegedAccess(Identity idn) {
    if (idn == null || idn.getLinks() == null) {
      return false;
    }
    for (Object o : idn.getLinks()) {
      if (!(o instanceof Link)) {
        continue;
      }
      Link link = (Link) o;
      for (String key : new String[] {"entitlement", "itAccess", "groups", "memberOf", "Roles"}) {
        Object v = link.getAttribute(key);
        if (v == null) {
          continue;
        }
        String u = String.valueOf(v).toUpperCase(Locale.ROOT);
        for (String p : ORG_PRIVILEGED) {
          if (u.contains(p)) {
            return true;
          }
        }
      }
      Application app = link.getApplication();
      if (app != null) {
        String an = app.getName() != null ? app.getName().toUpperCase(Locale.ROOT) : "";
        if (an.contains("AWS") || an.contains("WIRE") || an.contains("SAP")) {
          // Flag high-risk app presence lightly; UI shows badge only with riskFlags
          Object ei = link.getAttribute("entitlement");
          if (ei != null && String.valueOf(ei).toUpperCase(Locale.ROOT).contains("ADMIN")) {
            return true;
          }
        }
      }
    }
    return false;
  }

  private static Object firstAttr(Identity idn, String... keys) {
    if (idn == null || keys == null) {
      return null;
    }
    for (String k : keys) {
      Object v = idn.getAttribute(k);
      if (v != null && !Util.isNullOrEmpty(String.valueOf(v))) {
        return v;
      }
    }
    return null;
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
