package com.meridianbank.iiq.plugin.rest;

import java.io.ByteArrayInputStream;
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

import sailpoint.api.ManagedAttributer;
import sailpoint.api.PasswordPolice;
import sailpoint.api.SailPointContext;
import sailpoint.api.TaskManager;
import sailpoint.api.Workflower;
import sailpoint.api.Certificationer;
import sailpoint.connector.Connector;
import sailpoint.connector.ConnectorException;
import sailpoint.connector.ConnectorFactory;
import sailpoint.connector.DefaultApplicationFactory;
import sailpoint.connector.DefaultConnectorServices;
import sailpoint.object.Application;
import sailpoint.object.AuditEvent;
import sailpoint.object.BatchRequest;
import sailpoint.object.Bundle;
import sailpoint.object.Capability;
import sailpoint.object.Certification;
import sailpoint.object.CertificationAction;
import sailpoint.object.CertificationItem;
import sailpoint.object.Configuration;
import sailpoint.object.EmailTemplate;
import sailpoint.object.Filter;
import sailpoint.object.Form;
import sailpoint.object.GroupDefinition;
import sailpoint.object.Identity;
import sailpoint.object.Link;
import sailpoint.object.ManagedAttribute;
import sailpoint.object.Plugin;
import sailpoint.object.PolicyViolation;
import sailpoint.object.Profile;
import sailpoint.object.ProvisioningPlan;
import sailpoint.object.ProvisioningPlan.AccountRequest;
import sailpoint.object.ProvisioningPlan.AttributeRequest;
import sailpoint.object.QueryOptions;
import sailpoint.object.QuickLink;
import sailpoint.object.RoleIndex;
import sailpoint.object.SailPointObject;
import sailpoint.object.Schema;
import sailpoint.plugin.PluginsCache;
import sailpoint.server.Environment;
import sailpoint.object.TaskDefinition;
import sailpoint.object.TaskSchedule;
import sailpoint.object.WorkItem;
import sailpoint.object.Workflow;
import sailpoint.object.WorkflowLaunch;
import sailpoint.plugin.PluginInstaller;
import sailpoint.rest.plugin.BasePluginResource;
import sailpoint.rest.plugin.RequiredRight;
import sailpoint.server.Importer;
import sailpoint.service.plugin.PluginsService;
import sailpoint.tools.GeneralException;
import sailpoint.tools.Util;

/**
 * Meridian Custom APIs surface for MCP / ITSM — closes UI-VS-API gaps under {@code /mnbToolkit/agent}.
 *
 * <p>High-risk mutate ops require {@code mutateGovernanceEnabled}, {@code passwordResetEnabled},
 * or {@code advancedOpsEnabled}.
 */
@Path("mnbToolkit/agent")
@RequiredRight("MNBToolkitAgent")
public class MnbAgentResource extends BasePluginResource {

  private static final Logger log = Logger.getLogger(MnbAgentResource.class);

  @Override
  public String getPluginName() {
    return MnbToolkitPingResource.PLUGIN_NAME;
  }

  @GET
  @Path("gaps")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> gaps() {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-META");
    List<Map<String, Object>> rows = new ArrayList<>();
    rows.add(gap("UIAPI-01", "implemented", "tasks/run"));
    rows.add(gap("UIAPI-02", "implemented", "tasks/run"));
    rows.add(gap("UIAPI-03", "implemented", "accessRequests|access/grant|access/revoke"));
    rows.add(gap("UIAPI-04", "implemented", "workItems/*/decide"));
    rows.add(gap("UIAPI-05", "implemented", "certifications/items/*/decide"));
    rows.add(gap("UIAPI-06", "implemented", "sod/violations/*/mitigate"));
    rows.add(gap("UIAPI-07", "implemented", "applications/wizard"));
    rows.add(gap("UIAPI-08", "implemented", "applications/*/config"));
    rows.add(gap("UIAPI-09", "implemented", "populations"));
    rows.add(gap("UIAPI-10", "implemented", "workgroups/*/members"));
    rows.add(gap("UIAPI-11", "implemented", "identities/*/capabilities"));
    rows.add(gap("UIAPI-12", "implemented", "identities/*/password"));
    rows.add(gap("UIAPI-13", "implemented", "schedules"));
    rows.add(gap("UIAPI-14", "implemented", "reports/run"));
    rows.add(gap("UIAPI-15", "implemented", "forms"));
    rows.add(gap("UIAPI-16", "implemented", "quicklinks"));
    rows.add(gap("UIAPI-17", "implemented", "emailTemplates"));
    rows.add(gap("UIAPI-18", "implemented", "audit/events"));
    rows.add(gap("UIAPI-19", "implemented", "batchRequests"));
    rows.add(gap("UIAPI-20", "implemented", "accessHistory/status"));
    rows.add(gap("UIAPI-21", "implemented", "connectors/testConnection"));
    rows.add(gap("UIAPI-22", "implemented", "applications/*/nativeChangeDetection"));
    rows.add(gap("UIAPI-23", "implemented", "plugins"));
    rows.add(gap("UIAPI-24", "implemented", "system/config"));
    rows.add(gap("UIAPI-25", "implemented", "objects/export|import"));
    rows.add(gap("UIAPI-26", "implemented", "study/catalog"));
    rows.add(gap("UIAPI-27", "implemented", "mnbToolkit/ping"));
    rows.add(gap("UIAPI-28", "implemented", "entitlements|entitlements/promote"));
    rows.add(gap("UIAPI-29", "implemented", "roles|roles/*/profiles"));
    rows.add(gap("UIAPI-30", "implemented", "jml/*", "run_jml_event"));
    rows.add(gap("UIAPI-31", "implemented", "certifications/campaigns", "create_certification_campaign"));
    rows.add(gap("UIAPI-32", "implemented", "policies/sod", "create_sod_policy"));
    rows.add(gap("UIAPI-33", "implemented", "applications/*/accounts/*/password", "reset_target_password"));
    rows.add(gap("UIAPI-34", "implemented", "reports/*/download", "download_report_result"));
    rows.add(gap("UIAPI-35", "implemented", "executive/digest", "get_executive_digest"));
    rows.add(gap("UIAPI-36", "implemented", "batchRequests/*/execute", "execute_batch_request"));
    rows.add(gap("UIAPI-37", "implemented", "accounts/correlate", "correlate_account"));
    rows.add(gap("UIAPI-38", "implemented", "accessRequests/preview", "preview_access_request"));
    rows.add(gap("UIAPI-39", "implemented", "roles/mine", "mine_business_roles"));
    rows.add(gap("UIAPI-40", "implemented", "entitlements/classify", "classify_entitlements"));
    rows.add(gap("UIAPI-41", "implemented", "connectors/aggregate/groups", "trigger_group_aggregation"));
    rows.add(gap("UIAPI-42", "implemented", "workItems/*/forward", "forward_work_item"));
    rows.add(gap("UIAPI-43", "implemented", "forms/*/submit", "submit_form"));
    rows.add(gap("UIAPI-44", "implemented", "emailTemplates/*/send", "send_email_template"));
    rows.add(gap("UIAPI-45", "implemented", "audit/export", "export_audit_events"));
    rows.add(gap("UIAPI-46", "implemented", "capabilities", "create_capability"));
    rows.add(gap("UIAPI-47", "implemented", "objects/validate", "validate_sailpoint_object"));
    rows.add(gap("UIAPI-48", "implemented", "workflows/cases/*/resume", "resume_workflow_case"));
    rows.add(gap("UIAPI-49", "implemented", "risk/recalculate", "recalculate_risk_scores"));
    rows.add(gap("UIAPI-50", "implemented", "identities/*/reports/transitive", "list_transitive_reports"));
    rows.add(gap("UIAPI-51", "implemented", "applications/*/directory/ops", "directory_account_op"));
    rows.add(gap("UIAPI-52", "implemented", "identities/*/merge", "merge_identities"));
    rows.add(gap("UIAPI-53", "implemented", "applications/bulk/onboard", "bulk_onboard_applications"));
    rows.add(gap("UIAPI-54", "implemented", "provisioning/*/retry", "retry_provisioning_transaction"));
    rows.add(gap("UIAPI-55", "implemented", "alerts/rules", "configure_alert_rule"));
    rows.add(gap("UIAPI-56", "implemented", "system/services/*/restart", "restart_iiq_service"));
    rows.add(gap("UIAPI-57", "implemented", "scopes/assign", "assign_identity_scope"));
    rows.add(gap("UIAPI-58", "implemented", "identities/managers/rebuild", "rebuild_manager_hierarchy"));
    Map<String, Object> flags = new LinkedHashMap<>();
    flags.put("agentApiEnabled", MnbAgentSupport.flag(this, "agentApiEnabled"));
    flags.put("mutateGovernanceEnabled", MnbAgentSupport.flag(this, "mutateGovernanceEnabled"));
    flags.put("passwordResetEnabled", MnbAgentSupport.flag(this, "passwordResetEnabled"));
    flags.put("advancedOpsEnabled", MnbAgentSupport.flag(this, "advancedOpsEnabled"));
    flags.put("taskRunEnabled", MnbAgentSupport.flag(this, "taskRunEnabled"));
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("gaps", rows);
    data.put("flags", flags);
    return MnbAgentSupport.ok("UIAPI-META", data);
  }

  private static Map<String, Object> gap(String id, String status, String path) {
    return gap(id, status, path, null);
  }

  private static Map<String, Object> gap(String id, String status, String path, String mcpTool) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("id", id);
    m.put("status", status);
    m.put("path", path);
    m.put(
        "mcpTool",
        mcpTool != null ? mcpTool : "iiq_" + id.toLowerCase().replace('-', '_'));
    return m;
  }

  // —— Work items (UIAPI-04) ——

  @GET
  @Path("workItems")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listWorkItems(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-04");
    int lim = limit == null ? 50 : limit;
    return MnbAgentSupport.ok("UIAPI-04", MnbAgentSupport.listSummaries(getContext(), WorkItem.class, lim));
  }

  @GET
  @Path("workItems/{id}")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> getWorkItem(@PathParam("id") String id) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-04");
    WorkItem wi = MnbAgentSupport.requireByIdOrName(getContext(), WorkItem.class, id, "UIAPI-04");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", wi.getId());
    data.put("name", wi.getName());
    data.put("type", wi.getType() != null ? wi.getType().name() : null);
    data.put("state", wi.getState() != null ? wi.getState().name() : null);
    data.put("owner", wi.getOwner() != null ? wi.getOwner().getName() : null);
    data.put("requester", wi.getRequester() != null ? wi.getRequester().getName() : null);
    data.put("description", wi.getDescription());
    return MnbAgentSupport.ok("UIAPI-04", data);
  }

  @POST
  @Path("workItems/{id}/decide")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> decideWorkItem(@PathParam("id") String id, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-04");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String decision = MnbAgentSupport.str(body.get("decision"));
    String comment = MnbAgentSupport.str(body.get("comment"));
    if (Util.isNullOrEmpty(decision)) {
      throw MnbAgentSupport.error(400, "invalid_request", "decision required (approve|reject)", "UIAPI-04", null);
    }
    SailPointContext ctx = getContext();
    WorkItem wi = MnbAgentSupport.requireByIdOrName(ctx, WorkItem.class, id, "UIAPI-04");
    if (!Util.isNullOrEmpty(comment)) {
      wi.setCompletionComments(comment);
    }
    Workflower wf = new Workflower(ctx);
    if ("approve".equalsIgnoreCase(decision) || "finish".equalsIgnoreCase(decision)) {
      wf.finish(wi);
    } else if ("reject".equalsIgnoreCase(decision)) {
      wf.reject(wi);
    } else {
      throw MnbAgentSupport.error(400, "invalid_decision", "decision must be approve|reject", "UIAPI-04", null);
    }
    ctx.commitTransaction();
    log.warn("MNB agent workItem decide id=" + wi.getId() + " decision=" + decision + " by=" + ctx.getUserName());
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", wi.getId());
    data.put("decision", decision.toLowerCase());
    return MnbAgentSupport.ok("UIAPI-04", data);
  }

  // —— Access requests (UIAPI-03) ——

  @POST
  @Path("accessRequests")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> submitAccessRequest(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-03");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String workflowName = MnbAgentSupport.str(body.get("workflowName"));
    if (Util.isNullOrEmpty(workflowName)) {
      workflowName = "LCM Provisioning";
    }
    String identityName = MnbAgentSupport.str(body.get("identityName"));
    if (Util.isNullOrEmpty(identityName)) {
      throw MnbAgentSupport.error(400, "invalid_request", "identityName required", "UIAPI-03", null);
    }
    SailPointContext ctx = getContext();
    Identity target = ctx.getObjectByName(Identity.class, identityName);
    if (target == null) {
      throw MnbAgentSupport.error(404, "not_found", "Identity not found: " + identityName, "UIAPI-03", null);
    }
    Workflow wfObj = ctx.getObjectByName(Workflow.class, workflowName);
    if (wfObj == null) {
      throw MnbAgentSupport.error(
          404,
          "workflow_not_found",
          "Workflow not found: " + workflowName,
          "UIAPI-03",
          "Import LCM workflows or pass workflowName that exists in this lab");
    }
    @SuppressWarnings("unchecked")
    Map<String, Object> vars =
        body.get("variables") instanceof Map
            ? new HashMap<>((Map<String, Object>) body.get("variables"))
            : new HashMap<>();
    Object requestedItems = vars.get("requestedItems");
    Object plan = vars.get("plan");
    boolean hasItems =
        (requestedItems instanceof java.util.Collection && !((java.util.Collection<?>) requestedItems).isEmpty())
            || (requestedItems instanceof Object[] && ((Object[]) requestedItems).length > 0)
            || (plan instanceof ProvisioningPlan)
            || (plan instanceof Map && !((Map<?, ?>) plan).isEmpty());
    if (!hasItems) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "variables.requestedItems (or plan) required and non-empty",
          "UIAPI-03",
          "Pass at least one requestable role/entitlement item");
    }
    // LCM Provisioning requires a real ProvisioningPlan object (JSON Map is not enough).
    if (!(plan instanceof ProvisioningPlan) && requestedItems instanceof java.util.Collection) {
      @SuppressWarnings("unchecked")
      java.util.Collection<Object> items = (java.util.Collection<Object>) requestedItems;
      vars.put("plan", buildProvisioningPlan(ctx, target, items, vars));
    } else if (!(plan instanceof ProvisioningPlan) && plan instanceof Map) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "variables.plan must be built server-side; pass requestedItems instead of a JSON plan map",
          "UIAPI-03",
          "Send items as variables.requestedItems[{type,application,attribute,value|name}]");
    }
    vars.putIfAbsent("identityName", identityName);
    vars.putIfAbsent("launcher", ctx.getUserName());
    vars.putIfAbsent("flow", "AccessRequest");
    Workflower workflower = new Workflower(ctx);
    WorkflowLaunch launch = workflower.launch(wfObj, "mnb-agent-" + System.currentTimeMillis(), vars);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("workflowName", workflowName);
    data.put("identityName", identityName);
    if (launch != null) {
      data.put("launchId", launch.getTaskResult() != null ? launch.getTaskResult().getId() : null);
      data.put("workflowCaseId", launch.getWorkflowCase() != null ? launch.getWorkflowCase().getId() : null);
      data.put("launchStatus", launch.getStatus());
      if (launch.getStatus() != null
          && ("failed".equalsIgnoreCase(String.valueOf(launch.getStatus()))
              || "error".equalsIgnoreCase(String.valueOf(launch.getStatus())))) {
        throw MnbAgentSupport.error(
            502,
            "launch_failed",
            "Workflow launch failed: " + launch.getStatus(),
            "UIAPI-03",
            "Inspect TaskResult " + data.get("launchId") + " / LCM workflow args");
      }
    }
    return MnbAgentSupport.ok("UIAPI-03", data);
  }

  /**
   * Resolve a role or entitlement by display name and launch LCM AccessRequest / RemoveAccess.
   * NL-friendly: identityName + accessName (+ optional accessType role|entitlement).
   */
  @POST
  @Path("access/grant")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> grantAccess(Map<String, Object> body) throws GeneralException {
    return launchResolvedAccess(body, false);
  }

  @POST
  @Path("access/revoke")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> revokeAccess(Map<String, Object> body) throws GeneralException {
    return launchResolvedAccess(body, true);
  }

  private Map<String, Object> launchResolvedAccess(Map<String, Object> body, boolean revoke)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-03");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String identityName =
        firstNonEmpty(
            MnbAgentSupport.str(body.get("identityName")),
            MnbAgentSupport.str(body.get("identity")),
            MnbAgentSupport.str(body.get("userName")));
    String accessName =
        firstNonEmpty(
            MnbAgentSupport.str(body.get("accessName")),
            MnbAgentSupport.str(body.get("name")),
            MnbAgentSupport.str(body.get("role")),
            MnbAgentSupport.str(body.get("entitlement")));
    String accessType = MnbAgentSupport.str(body.get("accessType"));
    String justification = MnbAgentSupport.str(body.get("justification"));
    String workflowName = MnbAgentSupport.str(body.get("workflowName"));
    if (Util.isNullOrEmpty(workflowName)) {
      workflowName = "LCM Provisioning";
    }
    if (Util.isNullOrEmpty(identityName) || Util.isNullOrEmpty(accessName)) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "identityName and accessName required",
          "UIAPI-03",
          "Example: {identityName:\"anita.rao\", accessName:\"Wire Initiator\", accessType:\"role\"}");
    }
    SailPointContext ctx = getContext();
    Identity target = ctx.getObjectByName(Identity.class, identityName);
    if (target == null) {
      // display-name style: try first.last
      String dotted = identityName.trim().toLowerCase().replace(' ', '.');
      target = ctx.getObjectByName(Identity.class, dotted);
    }
    if (target == null) {
      throw MnbAgentSupport.error(404, "not_found", "Identity not found: " + identityName, "UIAPI-03", null);
    }
    Map<String, Object> item = resolveAccessItem(ctx, accessName, accessType);
    List<Object> items = new ArrayList<>();
    items.add(item);
    Map<String, Object> vars = new HashMap<>();
    vars.put("requestedItems", items);
    vars.put("flow", revoke ? "RemoveAccess" : "AccessRequest");
    if (!Util.isNullOrEmpty(justification)) {
      vars.put("comments", justification);
    }
    vars.put("plan", buildProvisioningPlan(ctx, target, items, vars));
    vars.putIfAbsent("identityName", target.getName());
    vars.putIfAbsent("launcher", ctx.getUserName());
    Workflow wfObj = ctx.getObjectByName(Workflow.class, workflowName);
    if (wfObj == null) {
      throw MnbAgentSupport.error(
          404, "workflow_not_found", "Workflow not found: " + workflowName, "UIAPI-03", null);
    }
    Workflower workflower = new Workflower(ctx);
    WorkflowLaunch launch =
        workflower.launch(wfObj, "mnb-agent-access-" + System.currentTimeMillis(), vars);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("workflowName", workflowName);
    data.put("identityName", target.getName());
    data.put("accessName", accessName);
    data.put("resolvedItem", item);
    data.put("action", revoke ? "revoke" : "grant");
    if (launch != null) {
      data.put("launchId", launch.getTaskResult() != null ? launch.getTaskResult().getId() : null);
      data.put("workflowCaseId", launch.getWorkflowCase() != null ? launch.getWorkflowCase().getId() : null);
      data.put("launchStatus", launch.getStatus());
      if (launch.getStatus() != null
          && ("failed".equalsIgnoreCase(String.valueOf(launch.getStatus()))
              || "error".equalsIgnoreCase(String.valueOf(launch.getStatus())))) {
        throw MnbAgentSupport.error(
            502,
            "launch_failed",
            "Workflow launch failed: " + launch.getStatus(),
            "UIAPI-03",
            "Inspect TaskResult " + data.get("launchId"));
      }
    }
    return MnbAgentSupport.ok("UIAPI-03", data);
  }

  private static Map<String, Object> resolveAccessItem(
      SailPointContext ctx, String accessName, String accessType) throws GeneralException {
    boolean preferRole =
        Util.isNullOrEmpty(accessType)
            || "role".equalsIgnoreCase(accessType)
            || "bundle".equalsIgnoreCase(accessType);
    boolean preferEnt =
        "entitlement".equalsIgnoreCase(accessType)
            || "managedAttribute".equalsIgnoreCase(accessType)
            || "group".equalsIgnoreCase(accessType);

    if (!preferEnt) {
      Bundle role = ctx.getObjectByName(Bundle.class, accessName);
      if (role == null) {
        QueryOptions qo = new QueryOptions();
        qo.addFilter(
            Filter.or(
                Filter.eq("displayName", accessName),
                Filter.like("name", accessName, Filter.MatchMode.START)));
        qo.setResultLimit(5);
        List<Bundle> hits = ctx.getObjects(Bundle.class, qo);
        if (hits != null && !hits.isEmpty()) {
          role = hits.get(0);
        }
      }
      if (role != null) {
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("type", "role");
        item.put("name", role.getName());
        item.put("id", role.getId());
        item.put("displayName", role.getDisplayName());
        return item;
      }
      if (preferRole && !Util.isNullOrEmpty(accessType)) {
        throw MnbAgentSupport.error(404, "not_found", "Role not found: " + accessName, "UIAPI-03", null);
      }
    }

    QueryOptions eqo = new QueryOptions();
    eqo.addFilter(
        Filter.or(
            Filter.eq("value", accessName),
            Filter.eq("displayName", accessName),
            Filter.like("value", accessName, Filter.MatchMode.START)));
    eqo.setResultLimit(5);
    List<ManagedAttribute> ents = ctx.getObjects(ManagedAttribute.class, eqo);
    if (ents == null || ents.isEmpty()) {
      throw MnbAgentSupport.error(
          404,
          "not_found",
          "No role or entitlement matched: " + accessName,
          "UIAPI-03",
          "Create/promote requestable roles or entitlements first");
    }
    ManagedAttribute ma = ents.get(0);
    Map<String, Object> item = new LinkedHashMap<>();
    item.put("type", "entitlement");
    item.put("application", ma.getApplication() != null ? ma.getApplication().getName() : null);
    item.put("attribute", ma.getAttribute());
    item.put("value", ma.getValue());
    item.put("displayName", ma.getDisplayName());
    item.put("id", ma.getId());
    return item;
  }

  // —— SoD (UIAPI-06) ——

  @GET
  @Path("sod/openCount")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> sodOpenCount(@QueryParam("policyPrefix") String policyPrefix)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-06");
    QueryOptions qo = new QueryOptions();
    qo.addFilter(Filter.eq("status", PolicyViolation.Status.Open));
    if (!Util.isNullOrEmpty(policyPrefix)) {
      qo.addFilter(Filter.like("policyName", policyPrefix, Filter.MatchMode.START));
    }
    int count = getContext().countObjects(PolicyViolation.class, qo);
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("openCount", count);
    data.put("policyPrefix", policyPrefix);
    return MnbAgentSupport.ok("UIAPI-06", data);
  }

  @GET
  @Path("sod/violations")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> sodList(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-06");
    QueryOptions qo = new QueryOptions();
    qo.addFilter(Filter.eq("status", PolicyViolation.Status.Open));
    qo.setResultLimit(limit == null ? 50 : Math.min(limit, 200));
    List<PolicyViolation> list = getContext().getObjects(PolicyViolation.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (list != null) {
      for (PolicyViolation v : list) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", v.getId());
        m.put("policyName", v.getPolicyName());
        m.put("constraintName", v.getConstraintName());
        m.put("identity", v.getIdentity() != null ? v.getIdentity().getName() : null);
        m.put("status", v.getStatus() != null ? v.getStatus().name() : null);
        rows.add(m);
      }
    }
    return MnbAgentSupport.ok("UIAPI-06", rows);
  }

  @POST
  @Path("sod/violations/{id}/mitigate")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> sodMitigate(@PathParam("id") String id, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-06");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    PolicyViolation v = MnbAgentSupport.requireByIdOrName(ctx, PolicyViolation.class, id, "UIAPI-06");
    v.setStatus(PolicyViolation.Status.Mitigated);
    v.setMitigator(ctx.getUserName());
    String comment = MnbAgentSupport.str(body.get("comment"));
    if (!Util.isNullOrEmpty(comment)) {
      v.setDescription(comment);
    }
    ctx.saveObject(v);
    ctx.commitTransaction();
    log.warn("MNB agent SoD mitigate id=" + v.getId() + " by=" + ctx.getUserName());
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", v.getId());
    data.put("status", "Mitigated");
    data.put("mitigator", v.getMitigator());
    return MnbAgentSupport.ok("UIAPI-06", data);
  }

  // —— Certifications (UIAPI-05) ——

  @GET
  @Path("certifications")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listCerts(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-05");
    return MnbAgentSupport.ok(
        "UIAPI-05", MnbAgentSupport.listSummaries(getContext(), Certification.class, limit == null ? 50 : limit));
  }

  @POST
  @Path("certifications/items/{id}/decide")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> decideCertItem(@PathParam("id") String id, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-05");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String decision = MnbAgentSupport.str(body.get("decision"));
    String comment = MnbAgentSupport.str(body.get("comment"));
    if (Util.isNullOrEmpty(decision)) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "decision required (approve|revoke|mitigate|acknowledge)", "UIAPI-05", null);
    }
    SailPointContext ctx = getContext();
    CertificationItem item = ctx.getObjectById(CertificationItem.class, id);
    if (item == null) {
      throw MnbAgentSupport.error(404, "not_found", "CertificationItem not found: " + id, "UIAPI-05", null);
    }
    Identity actor = ctx.getObjectByName(Identity.class, ctx.getUserName());
    CertificationAction action = item.getAction();
    if (action == null) {
      action = new CertificationAction();
      item.setAction(action);
    }
    String actorName = ctx.getUserName();
    if ("approve".equalsIgnoreCase(decision)) {
      action.approve(actorName, actor, comment, comment);
    } else if ("acknowledge".equalsIgnoreCase(decision)) {
      action.acknowledge(actorName, actor, comment, comment);
    } else if ("mitigate".equalsIgnoreCase(decision)) {
      Date exp = new Date(System.currentTimeMillis() + 30L * 24 * 3600 * 1000);
      action.mitigate(actorName, actor, comment, exp, comment);
    } else if ("revoke".equalsIgnoreCase(decision) || "remediate".equalsIgnoreCase(decision)) {
      action.remediate(
          actorName,
          actor,
          comment,
          CertificationAction.RemediationAction.OpenWorkItem,
          null,
          null,
          comment,
          null,
          null);
    } else {
      throw MnbAgentSupport.error(400, "invalid_decision", "unsupported decision", "UIAPI-05", null);
    }
    ctx.saveObject(item);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("itemId", item.getId());
    data.put("decision", decision.toLowerCase());
    return MnbAgentSupport.ok("UIAPI-05", data);
  }

  @POST
  @Path("certifications/{id}/sign")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> signCert(@PathParam("id") String id, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-05");
    SailPointContext ctx = getContext();
    Certification cert = MnbAgentSupport.requireByIdOrName(ctx, Certification.class, id, "UIAPI-05");
    Identity actor = ctx.getObjectByName(Identity.class, ctx.getUserName());
    Certificationer certificationer = new Certificationer(ctx);
    List<?> messages = certificationer.sign(cert, actor);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("certificationId", cert.getId());
    data.put("signedBy", ctx.getUserName());
    data.put("messages", messages != null ? messages.toString() : null);
    return MnbAgentSupport.ok("UIAPI-05", data);
  }

  // —— Populations / workgroups / capabilities ——

  @GET
  @Path("populations")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listPopulations(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-09");
    return MnbAgentSupport.ok(
        "UIAPI-09",
        MnbAgentSupport.listSummaries(getContext(), GroupDefinition.class, limit == null ? 50 : limit));
  }

  @GET
  @Path("populations/{name}")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> getPopulation(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-09");
    GroupDefinition gd = MnbAgentSupport.requireByIdOrName(getContext(), GroupDefinition.class, name, "UIAPI-09");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", gd.getId());
    data.put("name", gd.getName());
    data.put("filter", gd.getFilter() != null ? gd.getFilter().toString() : null);
    return MnbAgentSupport.ok("UIAPI-09", data);
  }

  @POST
  @Path("populations")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> createPopulation(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-09");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-09", null);
    }
    SailPointContext ctx = getContext();
    GroupDefinition gd = ctx.getObjectByName(GroupDefinition.class, name);
    if (gd == null) {
      gd = new GroupDefinition();
      gd.setName(name);
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      gd.setDescription(description);
    }
    String filterStr = MnbAgentSupport.str(body.get("filter"));
    if (Util.isNullOrEmpty(filterStr)) {
      filterStr = MnbAgentSupport.str(body.get("filterDefinition"));
    }
    if (!Util.isNullOrEmpty(filterStr)) {
      try {
        // IIQ Filter language, e.g. inactive == false
        gd.setFilter(Filter.compile(filterStr.trim()));
      } catch (Exception e) {
        throw MnbAgentSupport.error(
            400,
            "invalid_filter",
            "Cannot compile population filter: " + e.getMessage(),
            "UIAPI-09",
            "Use IIQ Filter language, e.g. inactive == false");
      }
    }
    gd.setPrivate(false);
    ctx.saveObject(gd);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", gd.getId());
    data.put("name", gd.getName());
    data.put("filter", gd.getFilter() != null ? gd.getFilter().toString() : null);
    data.put("description", gd.getDescription());
    return MnbAgentSupport.ok("UIAPI-09", data);
  }

  @GET
  @Path("populations/{name}/members")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> populationMembers(
      @PathParam("name") String name, @QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-09");
    GroupDefinition gd =
        MnbAgentSupport.requireByIdOrName(getContext(), GroupDefinition.class, name, "UIAPI-09");
    int lim = limit == null ? 25 : Math.min(limit, 200);
    QueryOptions qo = new QueryOptions();
    if (gd.getFilter() != null) {
      qo.addFilter(gd.getFilter());
    }
    qo.setResultLimit(lim);
    List<Identity> matches = getContext().getObjects(Identity.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (matches != null) {
      for (Identity id : matches) {
        if (id == null || id.isWorkgroup()) {
          continue;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", id.getId());
        m.put("name", id.getName());
        m.put("displayName", id.getDisplayableName());
        m.put("inactive", Boolean.valueOf(id.isInactive()));
        rows.add(m);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("population", gd.getName());
    data.put("filter", gd.getFilter() != null ? gd.getFilter().toString() : null);
    data.put("returned", rows.size());
    data.put("members", rows);
    return MnbAgentSupport.ok("UIAPI-09", data);
  }

  @POST
  @Path("populations/{name}/delete")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> deletePopulation(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-09");
    SailPointContext ctx = getContext();
    GroupDefinition gd = MnbAgentSupport.requireByIdOrName(ctx, GroupDefinition.class, name, "UIAPI-09");
    String id = gd.getId();
    String n = gd.getName();
    ctx.removeObject(gd);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("deleted", true);
    data.put("id", id);
    data.put("name", n);
    return MnbAgentSupport.ok("UIAPI-09", data);
  }

  @GET
  @Path("workgroups")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listWorkgroups(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-10");
    QueryOptions qo = new QueryOptions();
    qo.addFilter(Filter.eq("workgroup", true));
    qo.setResultLimit(limit == null ? 50 : Math.min(limit, 200));
    List<Identity> groups = getContext().getObjects(Identity.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (groups != null) {
      for (Identity g : groups) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", g.getId());
        m.put("name", g.getName());
        rows.add(m);
      }
    }
    return MnbAgentSupport.ok("UIAPI-10", rows);
  }

  @POST
  @Path("workgroups/{name}/members")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> workgroupMembers(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-10");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String op = MnbAgentSupport.str(body.get("op"));
    String member = MnbAgentSupport.str(body.get("member"));
    if (Util.isNullOrEmpty(op) || Util.isNullOrEmpty(member)) {
      throw MnbAgentSupport.error(400, "invalid_request", "op and member required", "UIAPI-10", null);
    }
    SailPointContext ctx = getContext();
    Identity wg = ctx.getObjectByName(Identity.class, name);
    if (wg == null || !wg.isWorkgroup()) {
      throw MnbAgentSupport.error(404, "not_found", "Workgroup not found: " + name, "UIAPI-10", null);
    }
    Identity mem = ctx.getObjectByName(Identity.class, member);
    if (mem == null) {
      throw MnbAgentSupport.error(404, "not_found", "Member identity not found: " + member, "UIAPI-10", null);
    }
    if ("add".equalsIgnoreCase(op)) {
      wg.add(mem);
    } else if ("remove".equalsIgnoreCase(op)) {
      wg.remove(mem);
    } else {
      throw MnbAgentSupport.error(400, "invalid_op", "op must be add|remove", "UIAPI-10", null);
    }
    ctx.saveObject(wg);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("workgroup", name);
    data.put("member", member);
    data.put("op", op.toLowerCase());
    return MnbAgentSupport.ok("UIAPI-10", data);
  }

  @POST
  @Path("identities/{name}/capabilities")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> identityCapabilities(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-11");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String op = MnbAgentSupport.str(body.get("op"));
    String capName = MnbAgentSupport.str(body.get("capability"));
    if (Util.isNullOrEmpty(op) || Util.isNullOrEmpty(capName)) {
      throw MnbAgentSupport.error(400, "invalid_request", "op and capability required", "UIAPI-11", null);
    }
    SailPointContext ctx = getContext();
    Identity id = ctx.getObjectByName(Identity.class, name);
    if (id == null) {
      throw MnbAgentSupport.error(404, "not_found", "Identity not found", "UIAPI-11", null);
    }
    Capability cap = ctx.getObjectByName(Capability.class, capName);
    if (cap == null) {
      throw MnbAgentSupport.error(404, "not_found", "Capability not found: " + capName, "UIAPI-11", null);
    }
    if ("assign".equalsIgnoreCase(op) || "add".equalsIgnoreCase(op)) {
      id.add(cap);
    } else if ("revoke".equalsIgnoreCase(op) || "remove".equalsIgnoreCase(op)) {
      id.remove(cap);
    } else {
      throw MnbAgentSupport.error(400, "invalid_op", "op must be assign|revoke", "UIAPI-11", null);
    }
    ctx.saveObject(id);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("identity", name);
    data.put("capability", capName);
    data.put("op", op.toLowerCase());
    return MnbAgentSupport.ok("UIAPI-11", data);
  }

  @POST
  @Path("identities/{name}/password")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> identityPassword(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requirePasswordMutate(this, "UIAPI-12");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String op = MnbAgentSupport.str(body.get("op"));
    SailPointContext ctx = getContext();
    Identity id = ctx.getObjectByName(Identity.class, name);
    if (id == null) {
      throw MnbAgentSupport.error(404, "not_found", "Identity not found", "UIAPI-12", null);
    }
    if ("unlock".equalsIgnoreCase(op)) {
      id.setFailedLoginAttempts(0);
      id.setAuthLockStart(null);
      ctx.saveObject(id);
      ctx.commitTransaction();
      Map<String, Object> unlocked = new LinkedHashMap<>();
      unlocked.put("identity", name);
      unlocked.put("op", "unlock");
      return MnbAgentSupport.ok("UIAPI-12", unlocked);
    }
    if ("set".equalsIgnoreCase(op) || "reset".equalsIgnoreCase(op)) {
      String password = MnbAgentSupport.str(body.get("password"));
      if (Util.isNullOrEmpty(password)) {
        throw MnbAgentSupport.error(400, "invalid_request", "password required for set/reset", "UIAPI-12", null);
      }
      PasswordPolice police = new PasswordPolice(ctx);
      police.setPassword(id, password, PasswordPolice.Expiry.USE_RESET_EXPIRY, true);
      ctx.commitTransaction();
      Map<String, Object> data = new LinkedHashMap<>();
      data.put("identity", name);
      data.put("op", "set");
      return MnbAgentSupport.ok("UIAPI-12", data);
    }
    throw MnbAgentSupport.error(400, "invalid_op", "op must be unlock|set|reset", "UIAPI-12", null);
  }

  // —— Schedules / reports / catalog lists ——

  @GET
  @Path("schedules")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listSchedules(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-13");
    return MnbAgentSupport.ok(
        "UIAPI-13", MnbAgentSupport.listSummaries(getContext(), TaskSchedule.class, limit == null ? 50 : limit));
  }

  @POST
  @Path("schedules")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> createSchedule(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-13");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    String taskDef = MnbAgentSupport.str(body.get("taskDefinition"));
    String cron = MnbAgentSupport.str(body.get("cron"));
    if (Util.isNullOrEmpty(name) || Util.isNullOrEmpty(taskDef)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name and taskDefinition required", "UIAPI-13", null);
    }
    SailPointContext ctx = getContext();
    TaskDefinition def = ctx.getObjectByName(TaskDefinition.class, taskDef);
    if (def == null) {
      throw MnbAgentSupport.error(404, "not_found", "TaskDefinition not found", "UIAPI-13", null);
    }
    TaskSchedule sched = new TaskSchedule();
    sched.setName(name);
    sched.setTaskDefinition(def);
    if (!Util.isNullOrEmpty(cron)) {
      sched.addCronExpression(cron);
    }
    ctx.saveObject(sched);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", sched.getId());
    data.put("name", sched.getName());
    return MnbAgentSupport.ok("UIAPI-13", data);
  }

  @POST
  @Path("reports/run")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> runReport(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-14");
    // Delegate semantics to task runner — reuse TaskManager directly (reports are TaskDefinitions)
    body = MnbAgentSupport.bodyOrEmpty(body);
    String taskName = MnbAgentSupport.str(body.get("taskName"));
    if (Util.isNullOrEmpty(taskName)) {
      throw MnbAgentSupport.error(400, "invalid_request", "taskName required", "UIAPI-14", null);
    }
    SailPointContext ctx = getContext();
    TaskManager tm = new TaskManager(ctx);
    TaskDefinition def = tm.getTaskDefinition(taskName);
    if (def == null) {
      throw MnbAgentSupport.error(404, "not_found", "TaskDefinition not found", "UIAPI-14", null);
    }
    @SuppressWarnings("unchecked")
    Map<String, Object> args =
        body.get("args") instanceof Map ? new HashMap<>((Map<String, Object>) body.get("args")) : new HashMap<>();
    sailpoint.object.TaskResult result = tm.runWithResult(def, args);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("taskName", taskName);
    data.put("taskResultId", result != null ? result.getId() : null);
    return MnbAgentSupport.ok("UIAPI-14", data);
  }

  @GET
  @Path("forms")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listForms(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-15");
    return MnbAgentSupport.ok(
        "UIAPI-15", MnbAgentSupport.listSummaries(getContext(), Form.class, limit == null ? 50 : limit));
  }

  @GET
  @Path("forms/{name}")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> getForm(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-15");
    Form form = MnbAgentSupport.requireByIdOrName(getContext(), Form.class, name, "UIAPI-15");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", form.getId());
    data.put("name", form.getName());
    data.put("description", form.getDescription());
    return MnbAgentSupport.ok("UIAPI-15", data);
  }

  @GET
  @Path("quicklinks")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listQuicklinks(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-16");
    return MnbAgentSupport.ok(
        "UIAPI-16", MnbAgentSupport.listSummaries(getContext(), QuickLink.class, limit == null ? 50 : limit));
  }

  @GET
  @Path("emailTemplates")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listEmailTemplates(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-17");
    return MnbAgentSupport.ok(
        "UIAPI-17",
        MnbAgentSupport.listSummaries(getContext(), EmailTemplate.class, limit == null ? 50 : limit));
  }

  @GET
  @Path("emailTemplates/{name}")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> getEmailTemplate(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-17");
    EmailTemplate t = MnbAgentSupport.requireByIdOrName(getContext(), EmailTemplate.class, name, "UIAPI-17");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", t.getId());
    data.put("name", t.getName());
    data.put("description", t.getDescription());
    return MnbAgentSupport.ok("UIAPI-17", data);
  }

  @GET
  @Path("audit/events")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> auditEvents(
      @QueryParam("limit") Integer limit, @QueryParam("action") String action) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-18");
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(limit == null ? 50 : Math.min(limit, 200));
    if (!Util.isNullOrEmpty(action)) {
      qo.addFilter(Filter.eq("action", action));
    }
    List<AuditEvent> events = getContext().getObjects(AuditEvent.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (events != null) {
      for (AuditEvent e : events) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", e.getId());
        m.put("action", e.getAction());
        m.put("source", e.getSource());
        m.put("target", e.getTarget());
        m.put("created", e.getCreated() != null ? e.getCreated().toInstant().toString() : null);
        rows.add(m);
      }
    }
    return MnbAgentSupport.ok("UIAPI-18", rows);
  }

  @POST
  @Path("batchRequests")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> batchRequest(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-19");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    String payload = MnbAgentSupport.str(body.get("payload"));
    if (Util.isNullOrEmpty(name)) {
      name = "mnb-agent-batch-" + System.currentTimeMillis();
    }
    SailPointContext ctx = getContext();
    BatchRequest br = new BatchRequest();
    br.setName(name);
    if (!Util.isNullOrEmpty(payload)) {
      br.setFileName("agent-payload.txt");
      br.setFileContents(payload);
    }
    ctx.saveObject(br);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", br.getId());
    data.put("name", br.getName());
    data.put(
        "note",
        "BatchRequest object created; schedule Batch Request Processing Task to execute");
    return MnbAgentSupport.ok("UIAPI-19", data);
  }

  @GET
  @Path("accessHistory/status")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> accessHistoryStatus() {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-20");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("accessHistoryConfigPresent", probeConfig(() -> Configuration.getAccessHistoryConfig()));
    data.put("identityAIConfigPresent", probeConfig(() -> Configuration.getIdentityAIConfig()));
    data.put("genAIConfigPresent", probeConfig(() -> Configuration.getGenAIConfig()));
    data.put(
        "note",
        "Presence of Configuration objects indicates module wiring; UI pages may still need licenses.");
    return MnbAgentSupport.ok("UIAPI-20", data);
  }

  private static boolean probeConfig(ConfigProbe probe) {
    try {
      return probe.get() != null;
    } catch (Throwable t) {
      return false;
    }
  }

  @FunctionalInterface
  private interface ConfigProbe {
    Configuration get() throws Exception;
  }

  // —— Applications (UIAPI-07/08/22) ——

  @POST
  @Path("applications/wizard")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> appWizard(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-07");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    String type = MnbAgentSupport.str(body.get("type"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-07", null);
    }
    if (Util.isNullOrEmpty(type)) {
      type = "DelimitedFile";
    }
    SailPointContext ctx = getContext();
    Application existing = ctx.getObjectByName(Application.class, name);
    boolean created = false;
    boolean overwrite =
        Boolean.TRUE.equals(body.get("overwrite"))
            || "true".equalsIgnoreCase(MnbAgentSupport.str(body.get("overwrite")));
    Application app;
    if (existing == null) {
      // Same path as IIQ UI "Add New Application": clone ConnectorRegistry template +
      // connector default attributes (connector, featuresString, parseType, filetransport, …).
      app = DefaultApplicationFactory.getDefaultApplicationByTemplate(type);
      if (app == null) {
        throw MnbAgentSupport.error(
            400,
            "unknown_type",
            "No ConnectorRegistry template for type: " + type,
            "UIAPI-07",
            "Use a registered type such as DelimitedFile");
      }
      app.setName(name);
      created = true;
    } else if (overwrite) {
      app = existing;
      // Repair incomplete wizard stubs (no connector class) without wiping existing attrs.
      if (Util.isNullOrEmpty(app.getConnector())) {
        enrichFromTemplate(app, type);
      }
      app.setType(type);
    } else {
      throw MnbAgentSupport.error(
          409,
          "conflict",
          "Application already exists: " + name,
          "UIAPI-07",
          "Pass overwrite=true or use /applications/stubs");
    }

    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      app.setDescription(description);
    }

    String ownerName = MnbAgentSupport.str(body.get("owner"));
    if (Util.isNullOrEmpty(ownerName)) {
      ownerName = ctx.getUserName();
    }
    if (!Util.isNullOrEmpty(ownerName) && app.getOwner() == null) {
      Identity owner = ctx.getObjectByName(Identity.class, ownerName);
      if (owner != null) {
        app.setOwner(owner);
      }
    } else if (!Util.isNullOrEmpty(ownerName)) {
      Identity owner = ctx.getObjectByName(Identity.class, ownerName);
      if (owner != null) {
        app.setOwner(owner);
      }
    }

    String features = MnbAgentSupport.str(body.get("featuresString"));
    if (!Util.isNullOrEmpty(features)) {
      app.setFeaturesString(features);
    }

    if (body.containsKey("authoritative")) {
      Object auth = body.get("authoritative");
      boolean authoritative =
          Boolean.TRUE.equals(auth) || "true".equalsIgnoreCase(MnbAgentSupport.str(auth));
      app.setAuthoritative(authoritative);
    }

    Map<String, Object> normalized = normalizeApplicationAttributes(type, body.get("attributes"));
    applySchemaHints(app, normalized);
    applyAttributeMap(app, normalized);
    ensureAccountSchema(app);

    ctx.saveObject(app);
    ctx.commitTransaction();
    Map<String, Object> data = summarizeApp(app);
    data.put("created", created);
    data.put("templateApplication", app.getAttributeValue(Application.ATTR_TEMPLATE_APPLICATION));
    List<String> hints = new ArrayList<>();
    if ("DelimitedFile".equalsIgnoreCase(type)) {
      Object file = app.getAttributeValue("file");
      if (file == null || Util.isNullOrEmpty(String.valueOf(file))) {
        hints.add("Set attributes.file to an absolute CSV path readable by the IIQ host");
      }
      Schema account = app.getAccountSchema();
      if (account == null || Util.isNullOrEmpty(account.getIdentityAttribute())) {
        hints.add("Discover schema / set account identityAttribute before aggregation");
      }
      hints.add(
          "Users are created by Account Aggregation (+ authoritative=true), not by this wizard");
    }
    if (!hints.isEmpty()) {
      data.put("nextSteps", hints);
    }
    return MnbAgentSupport.ok("UIAPI-07", data);
  }

  @POST
  @Path("applications/stubs")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> appStub(Map<String, Object> body) throws GeneralException {
    // Alias of wizard with minimal fields
    return appWizard(body);
  }

  @GET
  @Path("applications/{name}/config")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> getAppConfig(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-08");
    Application app = MnbAgentSupport.requireByIdOrName(getContext(), Application.class, name, "UIAPI-08");
    Map<String, Object> data = summarizeApp(app);
    data.put("attributes", redactMap(attributesToMap(app.getAttributes())));
    data.put("nativeChangeDetectionEnabled", app.isNativeChangeDetectionEnabled());
    data.put("nativeChangeOperations", app.getNativeChangeOperations());
    data.put("nativeChangeAttributes", app.getNativeChangeAttributes());
    return MnbAgentSupport.ok("UIAPI-08", data);
  }

  @POST
  @Path("applications/{name}/config")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> appConfig(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-08");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, name, "UIAPI-08");
    String type = MnbAgentSupport.str(body.get("type"));
    if (!Util.isNullOrEmpty(type)) {
      app.setType(type);
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      app.setDescription(description);
    }
    String features = MnbAgentSupport.str(body.get("featuresString"));
    if (!Util.isNullOrEmpty(features)) {
      app.setFeaturesString(features);
    }
    applyAttributeMap(app, body.get("attributes"));
    ctx.saveObject(app);
    ctx.commitTransaction();
    log.warn("MNB custom APIs application config updated name=" + app.getName() + " by=" + ctx.getUserName());
    return MnbAgentSupport.ok("UIAPI-08", summarizeApp(app));
  }

  @POST
  @Path("applications/{name}/nativeChangeDetection")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> nativeChangeDetection(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-22");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, name, "UIAPI-22");
    Object enabledObj = body.get("enabled");
    boolean enabled =
        Boolean.TRUE.equals(enabledObj)
            || "true".equalsIgnoreCase(MnbAgentSupport.str(enabledObj))
            || (enabledObj == null && body.containsKey("operations"));
    app.setNativeChangeDetectionEnabled(enabled);
    if (body.get("operations") instanceof List) {
      @SuppressWarnings("unchecked")
      List<Object> raw = (List<Object>) body.get("operations");
      List<String> ops = new ArrayList<>();
      for (Object o : raw) {
        if (o != null) {
          ops.add(String.valueOf(o));
        }
      }
      app.setNativeChangeOperations(ops);
    }
    if (body.get("attributes") instanceof List) {
      @SuppressWarnings("unchecked")
      List<Object> raw = (List<Object>) body.get("attributes");
      List<String> attrs = new ArrayList<>();
      for (Object o : raw) {
        if (o != null) {
          attrs.add(String.valueOf(o));
        }
      }
      app.setNativeChangeAttributes(attrs);
    }
    String scope = MnbAgentSupport.str(body.get("attributeScope"));
    if (!Util.isNullOrEmpty(scope)) {
      app.setNativeChangeAttributeScope(scope);
    }
    ctx.saveObject(app);
    ctx.commitTransaction();
    Map<String, Object> data = summarizeApp(app);
    data.put("nativeChangeDetectionEnabled", app.isNativeChangeDetectionEnabled());
    data.put("nativeChangeOperations", app.getNativeChangeOperations());
    data.put("nativeChangeAttributes", app.getNativeChangeAttributes());
    return MnbAgentSupport.ok("UIAPI-22", data);
  }

  @POST
  @Path("connectors/testConnection")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> testConnection(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-21");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String appName = MnbAgentSupport.str(body.get("application"));
    if (Util.isNullOrEmpty(appName)) {
      appName = MnbAgentSupport.str(body.get("name"));
    }
    if (Util.isNullOrEmpty(appName)) {
      throw MnbAgentSupport.error(400, "invalid_request", "application required", "UIAPI-21", null);
    }
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, appName, "UIAPI-21");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app.getName());
    data.put("type", app.getType());
    try {
      Connector connector = ConnectorFactory.getConnector(app, null);
      if (connector == null) {
        throw MnbAgentSupport.error(
            500, "connector_unavailable", "ConnectorFactory returned null", "UIAPI-21", null);
      }
      try {
        connector.setConnectorServices(new DefaultConnectorServices());
      } catch (Throwable ignore) {
        // some connectors do not require services
      }
      connector.testConfiguration();
      data.put("success", true);
      data.put("message", "testConfiguration completed without exception");
    } catch (ConnectorException e) {
      data.put("success", false);
      data.put("message", e.getMessage());
      data.put("errorClass", e.getClass().getSimpleName());
      log.warn("MNB testConnection failed app=" + app.getName() + " err=" + e.getMessage());
    } catch (Exception e) {
      data.put("success", false);
      data.put("message", e.getMessage());
      data.put("errorClass", e.getClass().getSimpleName());
    }
    return MnbAgentSupport.ok("UIAPI-21", data);
  }

  @GET
  @Path("system/config")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> getSystemConfig(@QueryParam("prefix") String prefix) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-24");
    Configuration cfg = getContext().getObjectByName(Configuration.class, Configuration.OBJ_NAME);
    if (cfg == null) {
      throw MnbAgentSupport.error(404, "not_found", "SystemConfiguration not found", "UIAPI-24", null);
    }
    Map<String, Object> attrs = redactMap(attributesToMap(cfg.getAttributes()));
    if (!Util.isNullOrEmpty(prefix)) {
      Map<String, Object> filtered = new LinkedHashMap<>();
      for (Map.Entry<String, Object> e : attrs.entrySet()) {
        if (e.getKey() != null && e.getKey().startsWith(prefix)) {
          filtered.put(e.getKey(), e.getValue());
        }
      }
      attrs = filtered;
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", Configuration.OBJ_NAME);
    data.put("attributes", attrs);
    return MnbAgentSupport.ok("UIAPI-24", data);
  }

  @POST
  @Path("system/config")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> systemConfig(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-24");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Configuration cfg = ctx.getObjectByName(Configuration.class, Configuration.OBJ_NAME);
    if (cfg == null) {
      throw MnbAgentSupport.error(404, "not_found", "SystemConfiguration not found", "UIAPI-24", null);
    }
    Object attrsObj = body.get("attributes");
    if (!(attrsObj instanceof Map)) {
      throw MnbAgentSupport.error(400, "invalid_request", "attributes map required", "UIAPI-24", null);
    }
    @SuppressWarnings("unchecked")
    Map<String, Object> attrs = (Map<String, Object>) attrsObj;
    int updated = 0;
    for (Map.Entry<String, Object> e : attrs.entrySet()) {
      if (e.getKey() == null || e.getKey().isEmpty()) {
        continue;
      }
      cfg.put(e.getKey(), e.getValue());
      updated++;
    }
    ctx.saveObject(cfg);
    ctx.commitTransaction();
    log.warn("MNB custom APIs system config updated keys=" + updated + " by=" + ctx.getUserName());
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("updatedKeys", updated);
    return MnbAgentSupport.ok("UIAPI-24", data);
  }

  @GET
  @Path("plugins")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listPlugins() throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-23");
    List<Plugin> plugins = getContext().getObjects(Plugin.class, new QueryOptions());
    List<Map<String, Object>> rows = new ArrayList<>();
    if (plugins != null) {
      for (Plugin p : plugins) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", p.getId());
        m.put("name", p.getName());
        m.put("displayName", p.getDisplayName());
        m.put("version", p.getVersion());
        m.put("disabled", p.isDisabled());
        m.put("installDate", p.getInstallDate() != null ? p.getInstallDate().toInstant().toString() : null);
        rows.add(m);
      }
    }
    return MnbAgentSupport.ok("UIAPI-23", rows);
  }

  @POST
  @Path("plugins/{name}/settings")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> updatePluginSettings(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    // Intentionally NOT gated on advancedOpsEnabled — settings enablement is required to turn
    // that flag on. Still requires agent right; first bootstrap can use OOTB /rest/plugins UI.
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Plugin plugin = MnbAgentSupport.requireByIdOrName(ctx, Plugin.class, name, "UIAPI-23");
    Object settingsObj = body.get("settings");
    if (!(settingsObj instanceof Map)) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "settings map required",
          "UIAPI-23",
          "Pass {\"settings\":{\"agentApiEnabled\":\"true\",...}}");
    }
    @SuppressWarnings("unchecked")
    Map<String, Object> raw = (Map<String, Object>) settingsObj;
    Map<String, String> settings = new LinkedHashMap<>();
    for (Map.Entry<String, Object> e : raw.entrySet()) {
      if (e.getKey() != null && e.getValue() != null) {
        settings.put(e.getKey(), String.valueOf(e.getValue()));
      }
    }
    if (settings.isEmpty()) {
      throw MnbAgentSupport.error(400, "invalid_request", "settings map empty", "UIAPI-23", null);
    }
    try {
      PluginsCache cache = Environment.getEnvironment().getPluginsCache();
      PluginsService svc = new PluginsService(ctx);
      svc.updateSettings(plugin, settings, cache);
      ctx.commitTransaction();
    } catch (Exception e) {
      throw MnbAgentSupport.error(
          500,
          "settings_update_failed",
          e.getMessage(),
          "UIAPI-23",
          "Fallback: Plugins UI → Meridian Custom APIs");
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", plugin.getName());
    data.put("updated", settings);
    data.put(
        "flags",
        Map.of(
            "agentApiEnabled", MnbAgentSupport.flag(this, "agentApiEnabled"),
            "taskRunEnabled", MnbAgentSupport.flag(this, "taskRunEnabled"),
            "mutateGovernanceEnabled", MnbAgentSupport.flag(this, "mutateGovernanceEnabled"),
            "passwordResetEnabled", MnbAgentSupport.flag(this, "passwordResetEnabled"),
            "advancedOpsEnabled", MnbAgentSupport.flag(this, "advancedOpsEnabled")));
    return MnbAgentSupport.ok("UIAPI-23", data);
  }

  @GET
  @Path("capabilities")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listCapabilities(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-11");
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(limit == null ? 100 : Math.min(limit, 500));
    List<Capability> caps = getContext().getObjects(Capability.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (caps != null) {
      for (Capability c : caps) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", c.getId());
        m.put("name", c.getName());
        m.put("displayName", c.getDisplayName());
        m.put("description", c.getDescription());
        rows.add(m);
      }
    }
    return MnbAgentSupport.ok("UIAPI-11", rows);
  }

  // —— Entitlement catalog (UIAPI-28) ——

  @GET
  @Path("entitlements")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listEntitlements(
      @QueryParam("application") String application,
      @QueryParam("attribute") String attribute,
      @QueryParam("value") String value,
      @QueryParam("requestable") Boolean requestable,
      @QueryParam("limit") Integer limit)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-28");
    SailPointContext ctx = getContext();
    QueryOptions qo = new QueryOptions();
    if (!Util.isNullOrEmpty(application)) {
      Application app = ctx.getObjectByName(Application.class, application);
      if (app == null) {
        throw MnbAgentSupport.error(404, "not_found", "Application not found: " + application, "UIAPI-28", null);
      }
      qo.addFilter(Filter.eq("application", app));
    }
    if (!Util.isNullOrEmpty(attribute)) {
      qo.addFilter(Filter.eq("attribute", attribute));
    }
    if (!Util.isNullOrEmpty(value)) {
      qo.addFilter(Filter.eq("value", value));
    }
    if (requestable != null) {
      qo.addFilter(Filter.eq("requestable", requestable));
    }
    qo.setResultLimit(limit == null ? 100 : Math.min(limit, 500));
    List<ManagedAttribute> mas = ctx.getObjects(ManagedAttribute.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (mas != null) {
      for (ManagedAttribute ma : mas) {
        rows.add(summarizeManagedAttribute(ma));
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("returned", rows.size());
    data.put("items", rows);
    return MnbAgentSupport.ok("UIAPI-28", data);
  }

  @POST
  @Path("entitlements")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> upsertEntitlement(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-28");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String appName = MnbAgentSupport.str(body.get("application"));
    String attribute = MnbAgentSupport.str(body.get("attribute"));
    String value = MnbAgentSupport.str(body.get("value"));
    if (Util.isNullOrEmpty(appName) || Util.isNullOrEmpty(attribute) || Util.isNullOrEmpty(value)) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "application, attribute, and value required", "UIAPI-28", null);
    }
    SailPointContext ctx = getContext();
    Application app = ctx.getObjectByName(Application.class, appName);
    if (app == null) {
      throw MnbAgentSupport.error(404, "not_found", "Application not found: " + appName, "UIAPI-28", null);
    }
    ManagedAttribute ma = ManagedAttributer.get(ctx, app, attribute, value);
    boolean created = false;
    if (ma == null) {
      ma = new ManagedAttribute(app, attribute, value);
      created = true;
    }
    String displayName = MnbAgentSupport.str(body.get("displayName"));
    if (!Util.isNullOrEmpty(displayName)) {
      ma.setDisplayName(displayName);
    } else if (Util.isNullOrEmpty(ma.getDisplayName())) {
      ma.setDisplayName(value);
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      ma.setDescription(description);
    }
    if (body.containsKey("requestable")) {
      Object req = body.get("requestable");
      boolean requestable =
          Boolean.TRUE.equals(req) || "true".equalsIgnoreCase(String.valueOf(req));
      ma.setRequestable(requestable);
    }
    String ownerName = MnbAgentSupport.str(body.get("owner"));
    if (!Util.isNullOrEmpty(ownerName)) {
      Identity owner = ctx.getObjectByName(Identity.class, ownerName);
      if (owner == null) {
        throw MnbAgentSupport.error(404, "not_found", "Owner identity not found: " + ownerName, "UIAPI-28", null);
      }
      ma.setOwner(owner);
    }
    ctx.saveObject(ma);
    ctx.commitTransaction();
    Map<String, Object> data = summarizeManagedAttribute(ma);
    data.put("created", created);
    return MnbAgentSupport.ok("UIAPI-28", data);
  }

  @POST
  @Path("entitlements/promote")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> promoteEntitlements(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-28");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String appName = MnbAgentSupport.str(body.get("application"));
    if (Util.isNullOrEmpty(appName)) {
      throw MnbAgentSupport.error(400, "invalid_request", "application required", "UIAPI-28", null);
    }
    String attribute = MnbAgentSupport.str(body.get("attribute"));
    SailPointContext ctx = getContext();
    Application app = ctx.getObjectByName(Application.class, appName);
    if (app == null) {
      throw MnbAgentSupport.error(404, "not_found", "Application not found: " + appName, "UIAPI-28", null);
    }
    if (Util.isNullOrEmpty(attribute)) {
      Schema schema = app.getAccountSchema();
      if (schema != null && !Util.isNullOrEmpty(schema.getGroupAttribute())) {
        attribute = schema.getGroupAttribute();
      } else {
        attribute = "itAccess";
      }
    }
    QueryOptions qo = new QueryOptions();
    qo.addFilter(Filter.eq("application", app));
    List<Link> links = ctx.getObjects(Link.class, qo);
    ManagedAttributer promoter = new ManagedAttributer(ctx);
    int linksScanned = 0;
    int promoted = 0;
    if (links != null) {
      for (Link link : links) {
        if (link == null) {
          continue;
        }
        linksScanned++;
        List<ManagedAttribute> created = promoter.promoteManagedAttributes(link);
        if (created != null) {
          promoted += created.size();
        }
      }
    }
    ctx.commitTransaction();
    // Also ensure distinct attribute values exist even if promote skipped some.
    java.util.LinkedHashSet<String> values = new java.util.LinkedHashSet<>();
    if (links != null) {
      for (Link link : links) {
        if (link == null) {
          continue;
        }
        Object raw = link.getAttribute(attribute);
        collectAttributeValues(raw, values);
      }
    }
    int upserted = 0;
    for (String v : values) {
      ManagedAttribute ma = ManagedAttributer.get(ctx, app, attribute, v);
      if (ma == null) {
        ma = new ManagedAttribute(app, attribute, v);
        ma.setDisplayName(v);
        // Lab default: not requestable until update_entitlement_metadata / catalog policy sets it.
        ma.setRequestable(false);
        ctx.saveObject(ma);
        upserted++;
      }
    }
    if (upserted > 0) {
      ctx.commitTransaction();
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", appName);
    data.put("attribute", attribute);
    data.put("linksScanned", linksScanned);
    data.put("promotedFromLinks", promoted);
    data.put("distinctValues", values.size());
    data.put("createdFromValues", upserted);
    return MnbAgentSupport.ok("UIAPI-28", data);
  }

  // —— Roles / Bundles (UIAPI-29) ——

  @GET
  @Path("roles")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> listRoles(
      @QueryParam("query") String query,
      @QueryParam("requestable") Boolean requestable,
      @QueryParam("limit") Integer limit)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-29");
    QueryOptions qo = new QueryOptions();
    if (!Util.isNullOrEmpty(query)) {
      qo.addFilter(
          Filter.or(Filter.like("name", query, Filter.MatchMode.ANYWHERE), Filter.like("displayName", query, Filter.MatchMode.ANYWHERE)));
    }
    qo.setResultLimit(limit == null ? 100 : Math.min(limit, 500));
    List<Bundle> bundles = getContext().getObjects(Bundle.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (bundles != null) {
      for (Bundle b : bundles) {
        Map<String, Object> row = summarizeBundle(b);
        if (requestable != null) {
          Boolean isReq = (Boolean) row.get("requestable");
          if (isReq == null || !isReq.equals(requestable)) {
            continue;
          }
        }
        rows.add(row);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("returned", rows.size());
    data.put("items", rows);
    return MnbAgentSupport.ok("UIAPI-29", data);
  }

  @POST
  @Path("roles")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> createRole(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-29");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-29", null);
    }
    SailPointContext ctx = getContext();
    Bundle existing = ctx.getObjectByName(Bundle.class, name);
    boolean created = existing == null;
    Bundle bundle = existing != null ? existing : new Bundle();
    if (created) {
      bundle.setName(name);
    }
    String type = MnbAgentSupport.str(body.get("type"));
    bundle.setType(Util.isNullOrEmpty(type) ? "business" : type);
    String displayName = MnbAgentSupport.str(body.get("displayName"));
    if (!Util.isNullOrEmpty(displayName)) {
      bundle.setDisplayName(displayName);
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      bundle.setDescription(description);
    }
    String ownerName = MnbAgentSupport.str(body.get("owner"));
    if (Util.isNullOrEmpty(ownerName)) {
      ownerName = "spadmin";
    }
    Identity owner = ctx.getObjectByName(Identity.class, ownerName);
    if (owner == null) {
      throw MnbAgentSupport.error(404, "not_found", "Owner identity not found: " + ownerName, "UIAPI-29", null);
    }
    bundle.setOwner(owner);
    boolean requestable = true;
    if (body.containsKey("requestable")) {
      Object req = body.get("requestable");
      requestable = Boolean.TRUE.equals(req) || "true".equalsIgnoreCase(String.valueOf(req));
    }
    // Persist requestable via Bundle attribute (RoleIndex permit APIs vary by IIQ build).
    bundle.setAttribute("requestable", Boolean.valueOf(requestable));
    try {
      RoleIndex idx = bundle.getRoleIndex();
      if (idx == null) {
        idx = new RoleIndex();
        bundle.setRoleIndex(idx);
      }
      // Reflective for builds that expose notPermittable on RoleIndex.
      java.lang.reflect.Method m = idx.getClass().getMethod("setNotPermittable", boolean.class);
      m.invoke(idx, Boolean.valueOf(!requestable));
    } catch (ReflectiveOperationException ignore) {
      // attribute above is enough for Meridian LCM catalog smoke
    }
    Object profilesObj = body.get("profiles");
    if (profilesObj instanceof java.util.Collection) {
      applyRoleProfiles(ctx, bundle, (java.util.Collection<?>) profilesObj, false);
    }
    ctx.saveObject(bundle);
    ctx.commitTransaction();
    Map<String, Object> data = summarizeBundle(bundle);
    data.put("created", created);
    return MnbAgentSupport.ok("UIAPI-29", data);
  }

  @POST
  @Path("roles/{name}/profiles")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> attachRoleProfiles(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-29");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Bundle bundle = MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, name, "UIAPI-29");
    Object profilesObj = body.get("profiles");
    if (!(profilesObj instanceof java.util.Collection) || ((java.util.Collection<?>) profilesObj).isEmpty()) {
      // Allow single profile shorthand: {application, attribute, value} or {application, constraints:[...]}
      if (!Util.isNullOrEmpty(MnbAgentSupport.str(body.get("application")))) {
        profilesObj = java.util.List.of(body);
      } else {
        throw MnbAgentSupport.error(
            400,
            "invalid_request",
            "profiles[] required (or application+constraints shorthand)",
            "UIAPI-29",
            null);
      }
    }
    boolean replace = Boolean.TRUE.equals(body.get("replace"));
    applyRoleProfiles(ctx, bundle, (java.util.Collection<?>) profilesObj, replace);
    ctx.saveObject(bundle);
    ctx.commitTransaction();
    Map<String, Object> data = summarizeBundle(bundle);
    data.put("profilesAttached", true);
    return MnbAgentSupport.ok("UIAPI-29", data);
  }

  @POST
  @Path("roles/{name}/delete")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> deleteRole(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-29");
    SailPointContext ctx = getContext();
    Bundle bundle = MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, name, "UIAPI-29");
    String id = bundle.getId();
    String n = bundle.getName();
    ctx.removeObject(bundle);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("deleted", true);
    data.put("id", id);
    data.put("name", n);
    return MnbAgentSupport.ok("UIAPI-29", data);
  }

  @POST
  @Path("objects/delete")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> deleteObject(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-25");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String className = MnbAgentSupport.str(body.get("className"));
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(className) || Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "className and name required", "UIAPI-25", null);
    }
    Class<? extends SailPointObject> type = resolveObjectClass(className, "UIAPI-25");
    SailPointContext ctx = getContext();
    SailPointObject obj = MnbAgentSupport.requireByIdOrName(ctx, type, name, "UIAPI-25");
    String id = obj.getId();
    String n = obj.getName();
    // Prefer Terminator for Identity/Application (cleans dependents); remove dependents for apps first.
    sailpoint.api.Terminator terminator = new sailpoint.api.Terminator(ctx);
    if (Application.class.isAssignableFrom(type)) {
      QueryOptions qo = new QueryOptions();
      qo.addFilter(Filter.eq("application", obj));
      List<ManagedAttribute> mas = ctx.getObjects(ManagedAttribute.class, qo);
      if (mas != null) {
        for (ManagedAttribute ma : mas) {
          if (ma != null) {
            terminator.deleteObject(ma);
          }
        }
      }
      terminator.deleteObject(obj);
    } else if (Identity.class.isAssignableFrom(type) || Bundle.class.isAssignableFrom(type)) {
      terminator.deleteObject(obj);
    } else {
      ctx.removeObject(obj);
    }
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("deleted", true);
    data.put("className", type.getSimpleName());
    data.put("id", id);
    data.put("name", n);
    return MnbAgentSupport.ok("UIAPI-25", data);
  }

  @POST
  @Path("plugins/{name}/state")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> pluginState(@PathParam("name") String name, Map<String, Object> body)
      throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-23");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Plugin plugin = MnbAgentSupport.requireByIdOrName(ctx, Plugin.class, name, "UIAPI-23");
    Object disabledObj = body.get("disabled");
    if (disabledObj == null) {
      throw MnbAgentSupport.error(400, "invalid_request", "disabled boolean required", "UIAPI-23", null);
    }
    boolean disabled =
        Boolean.TRUE.equals(disabledObj) || "true".equalsIgnoreCase(String.valueOf(disabledObj));
    plugin.setDisabled(disabled);
    ctx.saveObject(plugin);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("name", plugin.getName());
    data.put("disabled", plugin.isDisabled());
    data.put("note", "Plugin REST may require IIQ restart or PluginsCache reload to pick up fully");
    return MnbAgentSupport.ok("UIAPI-23", data);
  }

  @POST
  @Path("plugins/install")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> pluginsInstall(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-23");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String fileName = MnbAgentSupport.str(body.get("fileName"));
    String b64 = MnbAgentSupport.str(body.get("zipBase64"));
    if (Util.isNullOrEmpty(fileName) || Util.isNullOrEmpty(b64)) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "fileName and zipBase64 required",
          "UIAPI-23",
          "Or use POST /rest/plugins multipart from install.sh");
    }
    byte[] bytes;
    try {
      bytes = java.util.Base64.getDecoder().decode(b64);
    } catch (IllegalArgumentException e) {
      throw MnbAgentSupport.error(400, "invalid_base64", "zipBase64 is not valid Base64", "UIAPI-23", null);
    }
    SailPointContext ctx = getContext();
    try {
      PluginsService svc = new PluginsService(ctx);
      PluginsService.PluginInstallData data =
          new PluginsService.PluginInstallData(
              fileName, new ByteArrayInputStream(bytes), true, true, true, true);
      PluginInstaller.PluginInstallationResult result = svc.installPlugin(data, null);
      Map<String, Object> out = new LinkedHashMap<>();
      out.put("fileName", fileName);
      out.put("result", result != null ? result.toString() : "installed");
      return MnbAgentSupport.ok("UIAPI-23", out);
    } catch (Exception e) {
      throw MnbAgentSupport.error(
          500,
          "plugin_install_failed",
          e.getMessage(),
          "UIAPI-23",
          "Prefer ./pluginsrc/mnb-iam-toolkit/install.sh (multipart to /rest/plugins)");
    }
  }

  @GET
  @Path("objects/export")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> exportObject(
      @QueryParam("className") String className, @QueryParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-25");
    if (Util.isNullOrEmpty(className) || Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "className and name required", "UIAPI-25", null);
    }
    Class<? extends SailPointObject> type = resolveObjectClass(className, "UIAPI-25");
    SailPointObject obj = MnbAgentSupport.requireByIdOrName(getContext(), type, name, "UIAPI-25");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("className", type.getName());
    data.put("name", obj.getName());
    data.put("id", obj.getId());
    data.put("xml", obj.toXml());
    return MnbAgentSupport.ok("UIAPI-25", data);
  }

  @POST
  @Path("objects/import")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> importObject(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-25");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String xml = MnbAgentSupport.str(body.get("xml"));
    if (Util.isNullOrEmpty(xml)) {
      throw MnbAgentSupport.error(400, "invalid_request", "xml required", "UIAPI-25", null);
    }
    SailPointContext ctx = getContext();
    Importer importer = new Importer(ctx);
    importer.setScrubIds(Boolean.TRUE.equals(body.get("scrubIds")));
    importer.importXml(xml);
    ctx.commitTransaction();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("imported", true);
    data.put("bytes", xml.length());
    return MnbAgentSupport.ok("UIAPI-25", data);
  }

  @GET
  @Path("study/catalog")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> studyCatalog() throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-26");
    List<Map<String, Object>> catalog = new ArrayList<>();
    catalog.add(
        studyEntry(
            "AccessRequestApprovalAddins",
            "Study access-request approval widgets",
            "/plugin/rest/",
            "Not a production contract — lab study only"));
    catalog.add(
        studyEntry(
            "SWECertificationsAddins",
            "Study certification widgets",
            "/plugin/rest/",
            "Not a production contract — lab study only"));
    List<Plugin> plugins = getContext().getObjects(Plugin.class, new QueryOptions());
    List<Map<String, Object>> installedStudy = new ArrayList<>();
    if (plugins != null) {
      for (Plugin p : plugins) {
        String n = p.getName() != null ? p.getName() : "";
        String d = p.getDisplayName() != null ? p.getDisplayName() : "";
        if (n.toLowerCase().contains("cert")
            || n.toLowerCase().contains("approval")
            || n.toLowerCase().contains("addin")
            || d.toLowerCase().contains("study")
            || d.toLowerCase().contains("addin")) {
          Map<String, Object> m = new LinkedHashMap<>();
          m.put("name", p.getName());
          m.put("displayName", p.getDisplayName());
          m.put("version", p.getVersion());
          m.put("disabled", p.isDisabled());
          installedStudy.add(m);
        }
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("catalog", catalog);
    data.put("installedMatching", installedStudy);
    data.put("productionContract", "mnb_iam_toolkit (Meridian Custom APIs)");
    return MnbAgentSupport.ok("UIAPI-26", data);
  }

  private static Map<String, Object> studyEntry(String name, String purpose, String mount, String note) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("name", name);
    m.put("purpose", purpose);
    m.put("mountHint", mount);
    m.put("note", note);
    return m;
  }

  private static Map<String, Object> summarizeApp(Application app) {
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", app.getId());
    data.put("name", app.getName());
    data.put("type", app.getType());
    data.put("connector", app.getConnector());
    data.put("featuresString", app.getFeaturesString());
    data.put("icon", app.getIcon());
    data.put("authoritative", app.isAuthoritative());
    data.put("owner", app.getOwner() != null ? app.getOwner().getName() : null);
    Object file = app.getAttributeValue("file");
    if (file != null) {
      data.put("file", String.valueOf(file));
    }
    Schema account = app.getAccountSchema();
    if (account != null) {
      Map<String, Object> schema = new LinkedHashMap<>();
      schema.put("objectType", account.getObjectType());
      schema.put("identityAttribute", account.getIdentityAttribute());
      schema.put("displayAttribute", account.getDisplayAttribute());
      data.put("accountSchema", schema);
    }
    return data;
  }

  /**
   * Repair apps previously created as bare shells (no connector / features) by adopting
   * ConnectorRegistry + connector defaults without clobbering already-set attributes.
   */
  private static void enrichFromTemplate(Application app, String type) throws GeneralException {
    Application templated = DefaultApplicationFactory.getDefaultApplicationByTemplate(type);
    if (templated == null) {
      return;
    }
    if (Util.isNullOrEmpty(app.getConnector())) {
      app.setConnector(templated.getConnector());
    }
    if (Util.isNullOrEmpty(app.getFeaturesString())) {
      app.setFeaturesString(templated.getFeaturesString());
    }
    if (Util.isNullOrEmpty(app.getIcon())) {
      app.setIcon(templated.getIcon());
    }
    if (app.getAttributeValue(Application.ATTR_TEMPLATE_APPLICATION) == null
        && templated.getAttributeValue(Application.ATTR_TEMPLATE_APPLICATION) != null) {
      app.setAttribute(
          Application.ATTR_TEMPLATE_APPLICATION,
          templated.getAttributeValue(Application.ATTR_TEMPLATE_APPLICATION));
    }
    sailpoint.object.Attributes<String, Object> defaults = templated.getAttributes();
    if (defaults != null) {
      for (String key : defaults.keySet()) {
        if (app.getAttributeValue(key) == null) {
          app.setAttribute(key, defaults.get(key));
        }
      }
    }
  }

  /**
   * Map agent-friendly aliases onto real DelimitedFile connector keys. Drops invented keys that are
   * not part of the connector contract ({@code sourceType}, {@code autoImport}, …).
   */
  @SuppressWarnings("unchecked")
  private static Map<String, Object> normalizeApplicationAttributes(String type, Object attrsObj) {
    Map<String, Object> out = new LinkedHashMap<>();
    if (!(attrsObj instanceof Map)) {
      return out;
    }
    Map<String, Object> in = (Map<String, Object>) attrsObj;
    boolean delimited = type != null && type.toLowerCase().contains("delimited");

    for (Map.Entry<String, Object> e : in.entrySet()) {
      String key = e.getKey();
      if (key == null) {
        continue;
      }
      String k = key.trim();
      if (isInventedAgentAttribute(k)) {
        continue;
      }
      Object val = e.getValue();
      if ("filePath".equalsIgnoreCase(k) || "path".equalsIgnoreCase(k) || "fileName".equalsIgnoreCase(k)) {
        out.put("file", val);
        continue;
      }
      if ("parseHeader".equalsIgnoreCase(k)) {
        out.put("hasHeader", toBoolean(val));
        continue;
      }
      if ("delimiter".equalsIgnoreCase(k)) {
        out.put("delimiter", normalizeDelimiter(val));
        continue;
      }
      if ("hasHeader".equalsIgnoreCase(k)) {
        out.put("hasHeader", toBoolean(val));
        continue;
      }
      if ("identityAttribute".equalsIgnoreCase(k) || "nativeIdentity".equalsIgnoreCase(k)) {
        out.put("_schemaIdentityAttribute", val);
        continue;
      }
      if ("displayAttribute".equalsIgnoreCase(k)) {
        out.put("_schemaDisplayAttribute", val);
        continue;
      }
      out.put(k, val);
    }

    // fileFormat shortcuts (csv / comma_delimited) — consumed, not stored
    Object fileFormat = in.get("fileFormat");
    if (fileFormat == null) {
      fileFormat = in.get("sourceType");
    }
    if (delimited && fileFormat != null) {
      String ff = String.valueOf(fileFormat).trim().toLowerCase();
      if ("csv".equals(ff) || "comma".equals(ff) || "comma_delimited".equals(ff)) {
        out.putIfAbsent("delimiter", ",");
        out.putIfAbsent("hasHeader", Boolean.TRUE);
        out.putIfAbsent("parseType", "delimited");
        out.putIfAbsent("filetransport", "local");
      }
    }

    if (delimited && out.containsKey("file")) {
      out.putIfAbsent("filetransport", "local");
      out.putIfAbsent("parseType", "delimited");
      out.putIfAbsent("delimiter", ",");
      out.putIfAbsent("hasHeader", Boolean.TRUE);
    }
    return out;
  }

  private static boolean isInventedAgentAttribute(String key) {
    String k = key.toLowerCase();
    return "sourcetype".equals(k)
        || "autoimport".equals(k)
        || "userimport".equals(k)
        || "importmapping".equals(k)
        || "fileformat".equals(k);
  }

  private static Object normalizeDelimiter(Object val) {
    if (val == null) {
      return ",";
    }
    String s = String.valueOf(val).trim();
    if (s.isEmpty() || "comma".equalsIgnoreCase(s) || "csv".equalsIgnoreCase(s)) {
      return ",";
    }
    if ("tab".equalsIgnoreCase(s) || "\\t".equals(s)) {
      return "\t";
    }
    if ("pipe".equalsIgnoreCase(s)) {
      return "|";
    }
    if ("semicolon".equalsIgnoreCase(s)) {
      return ";";
    }
    return s;
  }

  private static Boolean toBoolean(Object val) {
    if (val instanceof Boolean) {
      return (Boolean) val;
    }
    if (val == null) {
      return Boolean.FALSE;
    }
    String s = String.valueOf(val).trim();
    return "true".equalsIgnoreCase(s) || "1".equals(s) || "yes".equalsIgnoreCase(s);
  }

  private static void applySchemaHints(Application app, Map<String, Object> normalized) {
    if (normalized == null || normalized.isEmpty()) {
      return;
    }
    Object idAttr = normalized.remove("_schemaIdentityAttribute");
    Object dispAttr = normalized.remove("_schemaDisplayAttribute");
    if (idAttr == null && dispAttr == null) {
      return;
    }
    ensureAccountSchema(app);
    Schema account = app.getAccountSchema();
    if (account == null) {
      return;
    }
    if (idAttr != null && !Util.isNullOrEmpty(String.valueOf(idAttr))) {
      account.setIdentityAttribute(String.valueOf(idAttr).trim());
    }
    if (dispAttr != null && !Util.isNullOrEmpty(String.valueOf(dispAttr))) {
      account.setDisplayAttribute(String.valueOf(dispAttr).trim());
    }
  }

  private static void ensureAccountSchema(Application app) {
    if (app.getAccountSchema() != null) {
      return;
    }
    Schema schema = new Schema("account", "account");
    schema.setNativeObjectType("account");
    schema.setObjectType("account");
    app.addSchema(schema);
  }

  @SuppressWarnings("unchecked")
  private static void applyAttributeMap(Application app, Object attrsObj) {
    if (!(attrsObj instanceof Map)) {
      return;
    }
    Map<String, Object> attrs = (Map<String, Object>) attrsObj;
    for (Map.Entry<String, Object> e : attrs.entrySet()) {
      if (e.getKey() != null && !e.getKey().startsWith("_")) {
        app.setAttribute(e.getKey(), e.getValue());
      }
    }
  }

  private static Map<String, Object> attributesToMap(sailpoint.object.Attributes<String, Object> attrs) {
    Map<String, Object> out = new LinkedHashMap<>();
    if (attrs == null) {
      return out;
    }
    for (String key : attrs.keySet()) {
      out.put(key, attrs.get(key));
    }
    return out;
  }

  private static Map<String, Object> redactMap(Map<String, Object> in) {
    Map<String, Object> out = new LinkedHashMap<>();
    for (Map.Entry<String, Object> e : in.entrySet()) {
      String k = e.getKey() != null ? e.getKey().toLowerCase() : "";
      if (k.contains("password") || k.contains("secret") || k.contains("token") || k.contains("key")) {
        out.put(e.getKey(), "***");
      } else {
        out.put(e.getKey(), e.getValue());
      }
    }
    return out;
  }

  private static Map<String, Object> summarizeManagedAttribute(ManagedAttribute ma) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("id", ma.getId());
    m.put("application", ma.getApplication() != null ? ma.getApplication().getName() : null);
    m.put("attribute", ma.getAttribute());
    m.put("value", ma.getValue());
    m.put("displayName", ma.getDisplayName());
    m.put("description", ma.getDescription());
    m.put("requestable", Boolean.valueOf(ma.isRequestable()));
    m.put("type", ma.getType());
    m.put("owner", ma.getOwner() != null ? ma.getOwner().getName() : null);
    return m;
  }

  private static Map<String, Object> summarizeBundle(Bundle b) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("id", b.getId());
    m.put("name", b.getName());
    m.put("displayName", b.getDisplayName());
    m.put("type", b.getType());
    m.put("description", b.getDescription());
    m.put("owner", b.getOwner() != null ? b.getOwner().getName() : null);
    boolean requestable = false;
    Object attrReq = b.getAttribute("requestable");
    if (attrReq != null) {
      requestable =
          Boolean.TRUE.equals(attrReq) || "true".equalsIgnoreCase(String.valueOf(attrReq));
    } else {
      RoleIndex idx = b.getRoleIndex();
      if (idx != null) {
        try {
          java.lang.reflect.Method meth = idx.getClass().getMethod("isNotPermittable");
          Object v = meth.invoke(idx);
          if (v instanceof Boolean) {
            requestable = !((Boolean) v).booleanValue();
          }
        } catch (ReflectiveOperationException ignore) {
          requestable = true;
        }
      } else {
        requestable = true;
      }
    }
    m.put("requestable", Boolean.valueOf(requestable));
    List<Map<String, Object>> profiles = new ArrayList<>();
    List<Profile> pls = b.getProfiles();
    if (pls != null) {
      for (Profile p : pls) {
        if (p == null) {
          continue;
        }
        Map<String, Object> pr = new LinkedHashMap<>();
        pr.put("id", p.getId());
        pr.put("name", p.getName());
        pr.put("application", p.getApplication() != null ? p.getApplication().getName() : null);
        List<String> cons = new ArrayList<>();
        if (p.getConstraints() != null) {
          for (Filter f : p.getConstraints()) {
            if (f != null) {
              cons.add(f.toString());
            }
          }
        }
        pr.put("constraints", cons);
        profiles.add(pr);
      }
    }
    m.put("profiles", profiles);
    return m;
  }

  private static void applyRoleProfiles(
      SailPointContext ctx, Bundle bundle, java.util.Collection<?> profilesObj, boolean replace)
      throws GeneralException {
    if (replace && bundle.getProfiles() != null) {
      bundle.setProfiles(new ArrayList<>());
    }
    for (Object raw : profilesObj) {
      if (!(raw instanceof Map)) {
        throw MnbAgentSupport.error(400, "invalid_request", "profiles entries must be objects", "UIAPI-29", null);
      }
      @SuppressWarnings("unchecked")
      Map<String, Object> pbody = (Map<String, Object>) raw;
      String appName = MnbAgentSupport.str(pbody.get("application"));
      if (Util.isNullOrEmpty(appName)) {
        throw MnbAgentSupport.error(400, "invalid_request", "profile.application required", "UIAPI-29", null);
      }
      Application app = ctx.getObjectByName(Application.class, appName);
      if (app == null) {
        throw MnbAgentSupport.error(404, "not_found", "Application not found: " + appName, "UIAPI-29", null);
      }
      Profile profile = new Profile();
      profile.setApplication(app);
      String pname = MnbAgentSupport.str(pbody.get("name"));
      if (!Util.isNullOrEmpty(pname)) {
        profile.setName(pname);
      }
      Object constraints = pbody.get("constraints");
      if (constraints instanceof java.util.Collection) {
        for (Object c : (java.util.Collection<?>) constraints) {
          profile.addConstraint(constraintFromBody(c));
        }
      } else {
        String attribute = MnbAgentSupport.str(pbody.get("attribute"));
        String value = MnbAgentSupport.str(pbody.get("value"));
        if (Util.isNullOrEmpty(attribute)) {
          attribute = "itAccess";
        }
        if (Util.isNullOrEmpty(value)) {
          throw MnbAgentSupport.error(
              400,
              "invalid_request",
              "profile needs constraints[] or attribute+value",
              "UIAPI-29",
              null);
        }
        profile.addConstraint(Filter.eq(attribute, value));
      }
      bundle.add(profile);
    }
  }

  private static Filter constraintFromBody(Object c) {
    if (c == null) {
      throw MnbAgentSupport.error(400, "invalid_request", "null constraint", "UIAPI-29", null);
    }
    if (c instanceof String) {
      try {
        return Filter.compile(((String) c).trim());
      } catch (Exception e) {
        throw MnbAgentSupport.error(
            400, "invalid_filter", "Cannot compile constraint: " + e.getMessage(), "UIAPI-29", null);
      }
    }
    if (c instanceof Map) {
      @SuppressWarnings("unchecked")
      Map<String, Object> m = (Map<String, Object>) c;
      String filterStr = MnbAgentSupport.str(m.get("filter"));
      if (!Util.isNullOrEmpty(filterStr)) {
        try {
          return Filter.compile(filterStr.trim());
        } catch (Exception e) {
          throw MnbAgentSupport.error(
              400, "invalid_filter", "Cannot compile constraint: " + e.getMessage(), "UIAPI-29", null);
        }
      }
      String attribute = MnbAgentSupport.str(m.get("attribute"));
      Object value = m.get("value");
      if (Util.isNullOrEmpty(attribute) || value == null) {
        throw MnbAgentSupport.error(
            400, "invalid_request", "constraint requires attribute+value or filter", "UIAPI-29", null);
      }
      return Filter.eq(attribute, value);
    }
    throw MnbAgentSupport.error(400, "invalid_request", "constraint must be string or object", "UIAPI-29", null);
  }

  private static void collectAttributeValues(Object raw, java.util.Set<String> values) {
    if (raw == null) {
      return;
    }
    if (raw instanceof java.util.Collection) {
      for (Object o : (java.util.Collection<?>) raw) {
        collectAttributeValues(o, values);
      }
      return;
    }
    if (raw.getClass().isArray()) {
      int len = java.lang.reflect.Array.getLength(raw);
      for (int i = 0; i < len; i++) {
        collectAttributeValues(java.lang.reflect.Array.get(raw, i), values);
      }
      return;
    }
    String s = String.valueOf(raw).trim();
    if (!Util.isNullOrEmpty(s)) {
      values.add(s);
    }
  }

  private static ProvisioningPlan buildProvisioningPlan(
      SailPointContext ctx, Identity target, java.util.Collection<Object> items, Map<String, Object> vars)
      throws GeneralException {
    ProvisioningPlan plan = new ProvisioningPlan();
    plan.setIdentity(target);
    boolean remove =
        "RemoveAccess".equalsIgnoreCase(MnbAgentSupport.str(vars.get("flow")))
            || "Revoke".equalsIgnoreCase(MnbAgentSupport.str(vars.get("flow")));
    ProvisioningPlan.Operation attrOp =
        remove ? ProvisioningPlan.Operation.Remove : ProvisioningPlan.Operation.Add;
    for (Object raw : items) {
      if (!(raw instanceof Map)) {
        throw MnbAgentSupport.error(
            400, "invalid_request", "requestedItems entries must be objects", "UIAPI-03", null);
      }
      @SuppressWarnings("unchecked")
      Map<String, Object> item = (Map<String, Object>) raw;
      String type = MnbAgentSupport.str(item.get("type"));
      if (Util.isNullOrEmpty(type)) {
        type = item.containsKey("attribute") ? "entitlement" : "role";
      }
      if ("role".equalsIgnoreCase(type) || "bundle".equalsIgnoreCase(type)) {
        String roleName =
            firstNonEmpty(
                MnbAgentSupport.str(item.get("name")),
                MnbAgentSupport.str(item.get("displayName")),
                MnbAgentSupport.str(item.get("id")));
        if (Util.isNullOrEmpty(roleName)) {
          throw MnbAgentSupport.error(400, "invalid_request", "role item requires name", "UIAPI-03", null);
        }
        Bundle role = ctx.getObjectByName(Bundle.class, roleName);
        if (role == null && !Util.isNullOrEmpty(MnbAgentSupport.str(item.get("id")))) {
          role = ctx.getObject(Bundle.class, MnbAgentSupport.str(item.get("id")));
        }
        if (role == null) {
          throw MnbAgentSupport.error(404, "not_found", "Role not found: " + roleName, "UIAPI-03", null);
        }
        AccountRequest iiqReq =
            new AccountRequest(
                AccountRequest.Operation.Modify, ProvisioningPlan.APP_IIQ, null, target.getName());
        iiqReq.add(new AttributeRequest(ProvisioningPlan.ATT_IIQ_ASSIGNED_ROLES, attrOp, role.getName()));
        plan.add(iiqReq);
      } else {
        String appName = MnbAgentSupport.str(item.get("application"));
        String attribute = MnbAgentSupport.str(item.get("attribute"));
        Object value = item.get("value");
        if (Util.isNullOrEmpty(appName) || Util.isNullOrEmpty(attribute) || value == null) {
          throw MnbAgentSupport.error(
              400,
              "invalid_request",
              "entitlement item requires application, attribute, value",
              "UIAPI-03",
              null);
        }
        String nativeId = null;
        List links = target.getLinks();
        if (links != null) {
          for (Object o : links) {
            if (!(o instanceof Link)) {
              continue;
            }
            Link link = (Link) o;
            if (appName.equals(link.getApplicationName())) {
              nativeId = link.getNativeIdentity();
              break;
            }
          }
        }
        AccountRequest.Operation acctOp =
            Util.isNullOrEmpty(nativeId)
                ? AccountRequest.Operation.Create
                : AccountRequest.Operation.Modify;
        AccountRequest ar = new AccountRequest(acctOp, appName, null, nativeId);
        ar.add(new AttributeRequest(attribute, attrOp, value));
        plan.add(ar);
      }
    }
    if (plan.getAccountRequests() == null || plan.getAccountRequests().isEmpty()) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "Could not build provisioning plan from requestedItems", "UIAPI-03", null);
    }
    return plan;
  }

  private static String firstNonEmpty(String... vals) {
    if (vals == null) {
      return null;
    }
    for (String v : vals) {
      if (!Util.isNullOrEmpty(v)) {
        return v;
      }
    }
    return null;
  }

  @SuppressWarnings("unchecked")
  private static Class<? extends SailPointObject> resolveObjectClass(String className, String gapId) {
    String cn = className.trim();
    if (!cn.contains(".")) {
      cn = "sailpoint.object." + cn;
    }
    if (!cn.startsWith("sailpoint.object.")) {
      throw MnbAgentSupport.error(
          400, "invalid_class", "Only sailpoint.object.* classes allowed", gapId, null);
    }
    try {
      Class<?> raw = Class.forName(cn);
      if (!SailPointObject.class.isAssignableFrom(raw)) {
        throw MnbAgentSupport.error(400, "invalid_class", "Not a SailPointObject: " + cn, gapId, null);
      }
      return (Class<? extends SailPointObject>) raw;
    } catch (ClassNotFoundException e) {
      throw MnbAgentSupport.error(400, "invalid_class", "Class not found: " + cn, gapId, null);
    }
  }
}
