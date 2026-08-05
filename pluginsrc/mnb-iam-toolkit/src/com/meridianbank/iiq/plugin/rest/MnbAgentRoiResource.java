package com.meridianbank.iiq.plugin.rest;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
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

import sailpoint.api.SailPointContext;
import sailpoint.object.Application;
import sailpoint.object.AttributeDefinition;
import sailpoint.object.Attributes;
import sailpoint.object.Bundle;
import sailpoint.object.Field;
import sailpoint.object.Form;
import sailpoint.object.Policy;
import sailpoint.object.QueryOptions;
import sailpoint.object.SODConstraint;
import sailpoint.object.Script;
import sailpoint.object.Workflow;
import sailpoint.object.Workflow.Step;
import sailpoint.rest.plugin.BasePluginResource;
import sailpoint.rest.plugin.RequiredRight;
import sailpoint.tools.GeneralException;
import sailpoint.tools.Util;

/**
 * High-ROI Custom APIs closing UIAPI-97/98/105–107/139 (workflow patch, form upsert,
 * connector deep config, SoD matrix import).
 */
@Path("mnbToolkit/agent")
@RequiredRight("MNBToolkitAgent")
public class MnbAgentRoiResource extends BasePluginResource {

  private static final Logger log = Logger.getLogger(MnbAgentRoiResource.class);

  @Override
  public String getPluginName() {
    return MnbToolkitPingResource.PLUGIN_NAME;
  }

  // —— UIAPI-97 Workflow list / get / patch ——

  @GET
  @Path("workflows")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> listWorkflows(@QueryParam("limit") Integer limit)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-97");
    int lim = limit == null ? 50 : Math.min(limit, 200);
    SailPointContext ctx = getContext();
    List<Map<String, Object>> rows = new ArrayList<>();
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(lim);
    for (Workflow wf : ctx.getObjects(Workflow.class, qo)) {
      if (wf == null) {
        continue;
      }
      rows.add(summarizeWorkflow(wf, false));
    }
    return MnbAgentSupport.ok("UIAPI-97", rows);
  }

  @GET
  @Path("workflows/{name}")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> getWorkflow(@PathParam("name") String name) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-97");
    Workflow wf =
        MnbAgentSupport.requireByIdOrName(getContext(), Workflow.class, name, "UIAPI-97");
    return MnbAgentSupport.ok("UIAPI-97", summarizeWorkflow(wf, true));
  }

  @POST
  @Path("workflows/{name}/patch")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> patchWorkflow(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-97");
    body = MnbAgentSupport.bodyOrEmpty(body);
    SailPointContext ctx = getContext();
    Workflow wf = MnbAgentSupport.requireByIdOrName(ctx, Workflow.class, name, "UIAPI-97");
    List<String> changed = new ArrayList<>();
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      wf.setDescription(description);
      changed.add("description");
    }
    Object varsObj = body.get("variables");
    if (varsObj instanceof Map) {
      @SuppressWarnings("unchecked")
      Map<String, Object> vars = (Map<String, Object>) varsObj;
      Attributes<String, Object> attrs = wf.getVariables();
      if (attrs == null) {
        attrs = new Attributes<>();
        wf.setVariables(attrs);
      }
      for (Map.Entry<String, Object> e : vars.entrySet()) {
        if (e.getKey() == null || e.getKey().startsWith("_")) {
          continue;
        }
        attrs.put(e.getKey(), e.getValue());
      }
      changed.add("variables");
    }
    // Optional: patch a named step (action/description/condition/args — not visual designer).
    String stepName = MnbAgentSupport.str(body.get("stepName"));
    if (!Util.isNullOrEmpty(stepName)) {
      Step step = wf.getStep(stepName);
      if (step == null) {
        step = findStep(wf, stepName);
      }
      if (step == null) {
        throw MnbAgentSupport.error(
            404, "not_found", "Workflow step not found: " + stepName, "UIAPI-97", null);
      }
      String stepDesc = MnbAgentSupport.str(body.get("stepDescription"));
      if (!Util.isNullOrEmpty(stepDesc)) {
        step.setDescription(stepDesc);
      }
      String action = MnbAgentSupport.str(body.get("stepAction"));
      if (!Util.isNullOrEmpty(action)) {
        step.setAction(action);
      }
      String condition = MnbAgentSupport.str(body.get("stepCondition"));
      if (!Util.isNullOrEmpty(condition)) {
        step.setCondition(condition);
      }
      Object argsObj = body.get("stepArgs");
      if (argsObj instanceof Map) {
        @SuppressWarnings("unchecked")
        Map<String, Object> argsMap = (Map<String, Object>) argsObj;
        List<Workflow.Arg> args = new ArrayList<>();
        for (Map.Entry<String, Object> e : argsMap.entrySet()) {
          if (e.getKey() == null || e.getKey().startsWith("_")) {
            continue;
          }
          Workflow.Arg arg = new Workflow.Arg(e.getKey(), e.getValue());
          args.add(arg);
        }
        step.setArgs(args);
      }
      changed.add("step:" + stepName);
    }
    if (changed.isEmpty()) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "Provide description, variables, and/or stepName (+ stepAction/stepArgs/…)",
          "UIAPI-97",
          null);
    }
    ctx.saveObject(wf);
    ctx.commitTransaction();
    log.warn(
        "MNB agent workflow patch name="
            + wf.getName()
            + " changed="
            + changed
            + " by="
            + ctx.getUserName());
    Map<String, Object> data = summarizeWorkflow(wf, true);
    data.put("changed", changed);
    return MnbAgentSupport.ok("UIAPI-97", data);
  }

  // —— UIAPI-98 Form upsert ——

  @POST
  @Path("forms")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> upsertForm(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-98");
    body = MnbAgentSupport.bodyOrEmpty(body);
    String name = MnbAgentSupport.str(body.get("name"));
    if (Util.isNullOrEmpty(name)) {
      throw MnbAgentSupport.error(400, "invalid_request", "name required", "UIAPI-98", null);
    }
    SailPointContext ctx = getContext();
    Form form = ctx.getObjectByName(Form.class, name);
    boolean created = false;
    if (form == null) {
      form = new Form();
      form.setName(name);
      created = true;
    }
    String description = MnbAgentSupport.str(body.get("description"));
    if (!Util.isNullOrEmpty(description)) {
      form.setDescription(description);
    }
    Object fieldsObj = body.get("fields");
    if (fieldsObj instanceof List) {
      // Replace field set when fields[] provided.
      List<Field> existing = form.getFields();
      if (existing != null) {
        for (Field f : new ArrayList<>(existing)) {
          if (f != null && f.getName() != null) {
            form.removeField(f.getName());
          }
        }
      }
      for (Object o : (List<?>) fieldsObj) {
        if (!(o instanceof Map)) {
          continue;
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> fm = (Map<String, Object>) o;
        String fname = MnbAgentSupport.str(fm.get("name"));
        if (Util.isNullOrEmpty(fname)) {
          continue;
        }
        Field field = new Field();
        field.setName(fname);
        String ftype =
            MnbAgentSupport.firstNonEmpty(
                MnbAgentSupport.str(fm.get("type")), AttributeDefinition.TYPE_STRING);
        field.setType(ftype);
        Object req = fm.get("required");
        if (req instanceof Boolean) {
          field.setRequired((Boolean) req);
        } else if (req != null) {
          field.setRequired(Boolean.parseBoolean(String.valueOf(req)));
        }
        if (fm.get("value") != null) {
          field.setValue(fm.get("value"));
        }
        String display = MnbAgentSupport.str(fm.get("displayName"));
        if (!Util.isNullOrEmpty(display)) {
          // Field uses displayName via AttributeDefinition hierarchy when available
          try {
            field.getClass().getMethod("setDisplayName", String.class).invoke(field, display);
          } catch (ReflectiveOperationException ignore) {
            // optional
          }
        }
        String scriptSrc = MnbAgentSupport.str(fm.get("script"));
        if (!Util.isNullOrEmpty(scriptSrc)) {
          field.setScript(new Script(scriptSrc));
        }
        form.add(field);
      }
    }
    ctx.saveObject(form);
    ctx.commitTransaction();
    log.warn(
        "MNB agent form upsert name="
            + form.getName()
            + " created="
            + created
            + " by="
            + ctx.getUserName());
    Map<String, Object> data = summarizeForm(form);
    data.put("created", created);
    return MnbAgentSupport.ok("UIAPI-98", data);
  }

  // —— UIAPI-139 SoD matrix import ——

  @POST
  @Path("policies/sod/matrix/import")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> importSodMatrix(Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireMutateGov(this, "UIAPI-139");
    body = MnbAgentSupport.bodyOrEmpty(body);
    boolean dryRun =
        body.get("dryRun") instanceof Boolean
            ? (Boolean) body.get("dryRun")
            : Boolean.parseBoolean(String.valueOf(body.getOrDefault("dryRun", "false")));
    boolean replaceConstraints =
        body.get("replaceConstraints") instanceof Boolean
            ? (Boolean) body.get("replaceConstraints")
            : Boolean.parseBoolean(
                String.valueOf(body.getOrDefault("replaceConstraints", "false")));
    String defaultPolicy =
        MnbAgentSupport.firstNonEmpty(
            MnbAgentSupport.str(body.get("policyName")), "MNB-SoD-Matrix-Import");
    List<Map<String, String>> rows = parseMatrixRows(body, defaultPolicy);
    if (rows.isEmpty()) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "Provide rows[] or csv (header: left,right[,policy][,constraint])",
          "UIAPI-139",
          null);
    }
    SailPointContext ctx = getContext();
    List<Map<String, Object>> applied = new ArrayList<>();
    Set<String> touchedPolicies = new LinkedHashSet<>();
    for (Map<String, String> row : rows) {
      String left = row.get("left");
      String right = row.get("right");
      String policyName = row.get("policy");
      String constraintName = row.get("constraint");
      if (Util.isNullOrEmpty(left) || Util.isNullOrEmpty(right)) {
        continue;
      }
      Map<String, Object> result = new LinkedHashMap<>();
      result.put("left", left);
      result.put("right", right);
      result.put("policy", policyName);
      result.put("constraint", constraintName);
      if (dryRun) {
        // Validate roles exist when possible
        Bundle lb = ctx.getObjectByName(Bundle.class, left);
        Bundle rb = ctx.getObjectByName(Bundle.class, right);
        result.put("leftFound", lb != null);
        result.put("rightFound", rb != null);
        result.put("dryRun", true);
        applied.add(result);
        continue;
      }
      Bundle leftBundle =
          MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, left, "UIAPI-139");
      Bundle rightBundle =
          MnbAgentSupport.requireByIdOrName(ctx, Bundle.class, right, "UIAPI-139");
      Policy policy = ctx.getObjectByName(Policy.class, policyName);
      boolean policyCreated = false;
      if (policy == null) {
        policy = new Policy();
        policy.setName(policyName);
        policy.setType("SOD");
        policy.setTypeKey("policy_type_sod");
        policy.setExecutor("sailpoint.policy.SODPolicyExecutor");
        policy.setConfigPage("sodpolicy.xhtml");
        policy.setState(Policy.State.Active);
        policyCreated = true;
      }
      if (replaceConstraints && policy.getSODConstraints() != null) {
        policy.getSODConstraints().clear();
      }
      SODConstraint constraint = null;
      if (policy.getSODConstraints() != null) {
        for (SODConstraint c : policy.getSODConstraints()) {
          if (c != null && constraintName.equals(c.getName())) {
            constraint = c;
            break;
          }
        }
      }
      boolean constraintCreated = false;
      if (constraint == null) {
        constraint = new SODConstraint();
        constraint.setName(constraintName);
        policy.addConstraint(constraint);
        constraintCreated = true;
      }
      constraint.addLeft(leftBundle);
      constraint.addRight(rightBundle);
      ctx.saveObject(policy);
      touchedPolicies.add(policy.getName());
      result.put("policyCreated", policyCreated);
      result.put("constraintCreated", constraintCreated);
      applied.add(result);
    }
    if (!dryRun) {
      ctx.commitTransaction();
      log.warn(
          "MNB agent SoD matrix import rows="
              + applied.size()
              + " policies="
              + touchedPolicies
              + " by="
              + ctx.getUserName());
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("dryRun", dryRun);
    data.put("rowCount", applied.size());
    data.put("policies", new ArrayList<>(touchedPolicies));
    data.put("rows", applied);
    return MnbAgentSupport.ok("UIAPI-139", data);
  }

  // —— UIAPI-105 AD / IQService deep config ——

  @POST
  @Path("applications/{name}/connector/ad")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> configureAdConnector(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-105");
    body = MnbAgentSupport.bodyOrEmpty(body);
    return applyConnectorAttrs(
        name,
        "UIAPI-105",
        body,
        Arrays.asList(
            "IQServiceHost",
            "IQServicePort",
            "IQServiceUser",
            "IQServicePassword",
            "forest",
            "domain",
            "user",
            "password",
            "port",
            "host",
            "useSSL",
            "pageSize",
            "searchDNs",
            "accountSearchDN",
            "groupSearchDN"));
  }

  // —— UIAPI-106 JDBC SQL map ——

  @POST
  @Path("applications/{name}/connector/jdbc")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> configureJdbcConnector(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-106");
    body = MnbAgentSupport.bodyOrEmpty(body);
    // Accept sqlMap as nested object → flatten to SQL_* attrs when present
    Object sqlMap = body.get("sqlMap");
    if (sqlMap instanceof Map) {
      @SuppressWarnings("unchecked")
      Map<String, Object> sm = (Map<String, Object>) sqlMap;
      for (Map.Entry<String, Object> e : sm.entrySet()) {
        if (e.getKey() == null) {
          continue;
        }
        body.put("SQL_" + e.getKey(), e.getValue());
      }
    }
    return applyConnectorAttrs(
        name,
        "UIAPI-106",
        body,
        Arrays.asList(
            "url",
            "driverClass",
            "user",
            "password",
            "SQLGetObject",
            "SQLGetObjectList",
            "SQLGetAccount",
            "SQLGetAccounts",
            "SQLCreateAccount",
            "SQLUpdateAccount",
            "SQLDeleteAccount",
            "testSQL",
            "jdbcURL",
            "useExecuteQuery"));
  }

  // —— UIAPI-107 OAuth / SCIM connector attrs ——

  @POST
  @Path("applications/{name}/connector/oauth")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> configureOauthConnector(
      @PathParam("name") String name, Map<String, Object> body) throws GeneralException {
    MnbAgentSupport.requireAdvancedOps(this, "UIAPI-107");
    body = MnbAgentSupport.bodyOrEmpty(body);
    return applyConnectorAttrs(
        name,
        "UIAPI-107",
        body,
        Arrays.asList(
            "tokenUrl",
            "clientId",
            "clientSecret",
            "grantType",
            "scope",
            "scimBaseUrl",
            "baseUrl",
            "audience",
            "authType",
            "oauth_headers",
            "username",
            "password",
            "resourceOwnerUsername",
            "resourceOwnerPassword"));
  }

  // —— helpers ——

  private Map<String, Object> applyConnectorAttrs(
      String appName, String gapId, Map<String, Object> body, List<String> allowedKeys)
      throws GeneralException {
    SailPointContext ctx = getContext();
    Application app = MnbAgentSupport.requireByIdOrName(ctx, Application.class, appName, gapId);
    Object attrsObj = body.get("attributes");
    Map<String, Object> attrs = new LinkedHashMap<>();
    if (attrsObj instanceof Map) {
      @SuppressWarnings("unchecked")
      Map<String, Object> nested = (Map<String, Object>) attrsObj;
      attrs.putAll(nested);
    }
    for (String key : allowedKeys) {
      if (body.containsKey(key) && body.get(key) != null) {
        attrs.put(key, body.get(key));
      }
    }
    // Also accept any SQL_* from JDBC flatten even if not in static list
    if ("UIAPI-106".equals(gapId)) {
      for (Map.Entry<String, Object> e : body.entrySet()) {
        if (e.getKey() != null && e.getKey().startsWith("SQL_") && e.getValue() != null) {
          attrs.put(e.getKey(), e.getValue());
        }
      }
    }
    if (attrs.isEmpty()) {
      throw MnbAgentSupport.error(
          400,
          "invalid_request",
          "No recognized connector attributes provided",
          gapId,
          "Pass known keys or attributes{} map");
    }
    List<String> applied = new ArrayList<>();
    for (Map.Entry<String, Object> e : attrs.entrySet()) {
      String key = e.getKey();
      if (key == null || key.startsWith("_")) {
        continue;
      }
      boolean allowed =
          allowedKeys.contains(key)
              || ("UIAPI-106".equals(gapId) && key.startsWith("SQL_"));
      if (!allowed) {
        continue;
      }
      app.setAttribute(key, e.getValue());
      applied.add(key);
    }
    if (applied.isEmpty()) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "No attributes matched allowlist for " + gapId, gapId, null);
    }
    ctx.saveObject(app);
    ctx.commitTransaction();
    log.warn(
        "MNB agent connector config gap="
            + gapId
            + " app="
            + app.getName()
            + " keys="
            + applied
            + " by="
            + ctx.getUserName());
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("application", app.getName());
    data.put("type", app.getType());
    data.put("appliedKeys", applied);
    Map<String, Object> redacted = new LinkedHashMap<>();
    for (String k : applied) {
      Object v = app.getAttributeValue(k);
      if (k.toLowerCase(Locale.ROOT).contains("password")
          || k.toLowerCase(Locale.ROOT).contains("secret")) {
        redacted.put(k, v == null ? null : "***");
      } else {
        redacted.put(k, v);
      }
    }
    data.put("attributes", redacted);
    return MnbAgentSupport.ok(gapId, data);
  }

  private static Step findStep(Workflow wf, String stepName) {
    if (wf == null || wf.getSteps() == null) {
      return null;
    }
    for (Object o : wf.getSteps()) {
      if (!(o instanceof Step)) {
        continue;
      }
      Step step = (Step) o;
      if (stepName.equals(step.getName())) {
        return step;
      }
    }
    return null;
  }

  private static Map<String, Object> summarizeWorkflow(Workflow wf, boolean detail) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("id", wf.getId());
    m.put("name", wf.getName());
    m.put("description", wf.getDescription());
    List<String> steps = new ArrayList<>();
    if (wf.getSteps() != null) {
      for (Object o : wf.getSteps()) {
        if (o instanceof Step) {
          Step s = (Step) o;
          if (s.getName() != null) {
            steps.add(s.getName());
          }
        }
      }
    }
    m.put("stepNames", steps);
    m.put("stepCount", steps.size());
    if (detail && wf.getVariables() != null) {
      Map<String, Object> vars = new LinkedHashMap<>();
      for (Object key : wf.getVariables().keySet()) {
        if (key == null) {
          continue;
        }
        String k = String.valueOf(key);
        Object v = wf.getVariables().get(key);
        if (k.toLowerCase(Locale.ROOT).contains("password")) {
          vars.put(k, v == null ? null : "***");
        } else {
          vars.put(k, v);
        }
      }
      m.put("variables", vars);
    }
    return m;
  }

  private static Map<String, Object> summarizeForm(Form form) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("id", form.getId());
    m.put("name", form.getName());
    m.put("description", form.getDescription());
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
        fm.put("displayName", f.getDisplayName());
        fm.put("displayType", f.getDisplayType());
        fields.add(fm);
      }
    }
    m.put("fields", fields);
    m.put("fieldCount", fields.size());
    return m;
  }

  @SuppressWarnings("unchecked")
  private static List<Map<String, String>> parseMatrixRows(
      Map<String, Object> body, String defaultPolicy) {
    List<Map<String, String>> out = new ArrayList<>();
    Object rowsObj = body.get("rows");
    if (rowsObj instanceof List) {
      int i = 0;
      for (Object o : (List<?>) rowsObj) {
        i++;
        if (!(o instanceof Map)) {
          continue;
        }
        Map<String, Object> r = (Map<String, Object>) o;
        String left =
            MnbAgentSupport.firstNonEmpty(
                MnbAgentSupport.str(r.get("left")),
                MnbAgentSupport.str(r.get("leftRole")),
                MnbAgentSupport.str(r.get("leftRoles")));
        String right =
            MnbAgentSupport.firstNonEmpty(
                MnbAgentSupport.str(r.get("right")),
                MnbAgentSupport.str(r.get("rightRole")),
                MnbAgentSupport.str(r.get("rightRoles")));
        String policy =
            MnbAgentSupport.firstNonEmpty(
                MnbAgentSupport.str(r.get("policy")),
                MnbAgentSupport.str(r.get("policyName")),
                defaultPolicy);
        String constraint =
            MnbAgentSupport.firstNonEmpty(
                MnbAgentSupport.str(r.get("constraint")),
                MnbAgentSupport.str(r.get("constraintName")),
                policy + "-c" + i);
        if (!Util.isNullOrEmpty(left) && !Util.isNullOrEmpty(right)) {
          Map<String, String> row = new LinkedHashMap<>();
          row.put("left", left.trim());
          row.put("right", right.trim());
          row.put("policy", policy.trim());
          row.put("constraint", constraint.trim());
          out.add(row);
        }
      }
    }
    String csv = MnbAgentSupport.str(body.get("csv"));
    if (!Util.isNullOrEmpty(csv)) {
      String[] lines = csv.split("\\r?\\n");
      boolean headerSkipped = false;
      int i = 0;
      for (String line : lines) {
        if (line == null) {
          continue;
        }
        line = line.trim();
        if (line.isEmpty() || line.startsWith("#")) {
          continue;
        }
        String[] cols = line.split(",", -1);
        if (!headerSkipped
            && cols.length >= 2
            && cols[0].toLowerCase(Locale.ROOT).contains("left")) {
          headerSkipped = true;
          continue;
        }
        headerSkipped = true;
        if (cols.length < 2) {
          continue;
        }
        i++;
        String left = cols[0].trim();
        String right = cols[1].trim();
        String policy = cols.length > 2 && !cols[2].trim().isEmpty() ? cols[2].trim() : defaultPolicy;
        String constraint =
            cols.length > 3 && !cols[3].trim().isEmpty()
                ? cols[3].trim()
                : policy + "-c" + i;
        if (!left.isEmpty() && !right.isEmpty()) {
          Map<String, String> row = new LinkedHashMap<>();
          row.put("left", left);
          row.put("right", right);
          row.put("policy", policy);
          row.put("constraint", constraint);
          out.add(row);
        }
      }
    }
    return out;
  }
}
