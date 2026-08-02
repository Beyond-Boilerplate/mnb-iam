package com.meridianbank.iiq.plugin.rest;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.MediaType;

import sailpoint.api.SailPointContext;
import sailpoint.object.Application;
import sailpoint.object.AuditEvent;
import sailpoint.object.Bundle;
import sailpoint.object.Capability;
import sailpoint.object.Certification;
import sailpoint.object.CertificationAction;
import sailpoint.object.CertificationEntity;
import sailpoint.object.CertificationItem;
import sailpoint.object.Filter;
import sailpoint.object.Identity;
import sailpoint.object.Link;
import sailpoint.object.ManagedAttribute;
import sailpoint.object.PolicyViolation;
import sailpoint.object.ProvisioningTransaction;
import sailpoint.object.QueryOptions;
import sailpoint.object.TaskResult;
import sailpoint.object.WorkItem;
import sailpoint.rest.plugin.BasePluginResource;
import sailpoint.rest.plugin.RequiredRight;
import sailpoint.tools.GeneralException;
import sailpoint.tools.Util;

/**
 * Meridian Console composite APIs for Teller Waves 1–3+ surfaces (UIAPI-60+).
 */
@Path("mnbToolkit/agent/console")
@RequiredRight("MNBToolkitAgent")
public class MnbConsoleResource extends BasePluginResource {

  private static final Pattern HR_KEY = Pattern.compile("^MNB\\d{5}$");
  private static final String[] PRIVILEGED = {
    "AWS_ADMIN", "WIRE_INIT", "WIRE_APPR", "SAP_FI", "CORE", "GL_POST"
  };

  @Override
  public String getPluginName() {
    return MnbToolkitPingResource.PLUGIN_NAME;
  }

  @GET
  @Path("orphans")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> orphans(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-60");
    int lim = limit == null ? 200 : Math.max(1, Math.min(limit, 1000));
    SailPointContext ctx = getContext();

    List<Map<String, Object>> loginNamed = new ArrayList<>();
    List<Map<String, Object>> uncorrelated = new ArrayList<>();

    QueryOptions iqo = new QueryOptions();
    iqo.setResultLimit(5000);
    List<Identity> identities = ctx.getObjects(Identity.class, iqo);
    Map<String, Identity> byName = new HashMap<>();
    Map<String, Identity> byEmail = new HashMap<>();
    if (identities != null) {
      for (Identity idn : identities) {
        if (idn == null || idn.isWorkgroup()) {
          continue;
        }
        byName.put(idn.getName(), idn);
        if (!Util.isNullOrEmpty(idn.getEmail())) {
          byEmail.put(idn.getEmail().toLowerCase(Locale.ROOT), idn);
        }
      }
      for (Identity idn : identities) {
        if (idn == null || idn.isWorkgroup()) {
          continue;
        }
        String name = idn.getName();
        if (name == null || !name.contains(".") || HR_KEY.matcher(name).matches()) {
          continue;
        }
        if ("spadmin".equalsIgnoreCase(name)) {
          continue;
        }
        Identity twin = null;
        if (!Util.isNullOrEmpty(idn.getEmail())) {
          twin = byEmail.get(idn.getEmail().toLowerCase(Locale.ROOT));
          if (twin != null && twin.getId().equals(idn.getId())) {
            twin = null;
          }
        }
        if (twin == null || !HR_KEY.matcher(twin.getName() != null ? twin.getName() : "").matches()) {
          // Prefer any HR-key identity sharing email local-part via scan
          for (Identity cand : byName.values()) {
            if (cand.getId().equals(idn.getId())) {
              continue;
            }
            if (HR_KEY.matcher(cand.getName() != null ? cand.getName() : "").matches()
                && emailsMatch(idn, cand)) {
              twin = cand;
              break;
            }
          }
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("orphanName", name);
        row.put("orphanDisplayName", idn.getDisplayableName());
        row.put("orphanId", idn.getId());
        row.put("email", idn.getEmail());
        row.put("accountCount", idn.getLinks() != null ? idn.getLinks().size() : 0);
        row.put("apps", linkAppNames(idn));
        row.put("twinName", twin != null ? twin.getName() : null);
        row.put("twinDisplayName", twin != null ? twin.getDisplayableName() : null);
        row.put("disposition", twin != null ? "merge" : "review");
        loginNamed.add(row);
        if (loginNamed.size() >= lim) {
          break;
        }
      }
    }

    QueryOptions lqo = new QueryOptions();
    lqo.addFilter(Filter.isnull("identity"));
    lqo.setResultLimit(lim);
    List<Link> orphans = ctx.getObjects(Link.class, lqo);
    if (orphans != null) {
      for (Link link : orphans) {
        if (link == null) {
          continue;
        }
        Map<String, Object> row = new LinkedHashMap<>();
        Application app = link.getApplication();
        row.put("application", app != null ? app.getName() : null);
        row.put("nativeIdentity", link.getNativeIdentity());
        row.put("displayName", link.getDisplayName());
        Object eid = link.getAttribute("employeeId");
        if (eid == null) {
          eid = link.getAttribute("userId");
        }
        row.put("employeeId", eid != null ? String.valueOf(eid) : null);
        row.put("email", link.getAttribute("email"));
        row.put("privileged", isPrivilegedLink(link));
        row.put("disposition", eid != null ? "correlate" : "disable-or-exception");
        uncorrelated.add(row);
      }
    }

    Map<String, Object> data = new LinkedHashMap<>();
    data.put("loginNamedOrphans", loginNamed);
    data.put("loginNamedCount", loginNamed.size());
    data.put("uncorrelatedAccounts", uncorrelated);
    data.put("uncorrelatedCount", uncorrelated.size());
    data.put(
        "guidance",
        "Merge login-named cubes into MNB##### keepers; correlate uncorrelated via employeeId→userId; never create-identities on targets.");
    return MnbAgentSupport.ok("UIAPI-60", data);
  }

  @GET
  @Path("pipeline")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> pipeline(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-61");
    int lim = limit == null ? 40 : Math.max(1, Math.min(limit, 100));
    SailPointContext ctx = getContext();
    QueryOptions qo = new QueryOptions();
    qo.addOrdering("created", false);
    qo.setResultLimit(300);
    List<TaskResult> results = ctx.getObjects(TaskResult.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    String[] interesting = {
      "Aggregate", "Aggregation", "Refresh", "MNB-", "Identity Refresh", "Account Aggregation"
    };
    if (results != null) {
      for (TaskResult tr : results) {
        if (tr == null || tr.getName() == null) {
          continue;
        }
        String n = tr.getName();
        boolean match = false;
        for (String token : interesting) {
          if (n.contains(token)) {
            match = true;
            break;
          }
        }
        if (!match) {
          continue;
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", tr.getId());
        row.put("name", n);
        row.put(
            "completionStatus",
            tr.getCompletionStatus() != null ? tr.getCompletionStatus().name() : null);
        row.put("launched", tr.getLaunched());
        row.put("completed", tr.getCompleted());
        row.put("messages", tr.getMessages() != null ? tr.getMessages().size() : 0);
        long durMs = 0L;
        Date launched = tr.getLaunched();
        Date completed = tr.getCompleted();
        if (launched != null && completed != null) {
          durMs = completed.getTime() - launched.getTime();
        }
        row.put("durationMs", durMs);
        rows.add(row);
        if (rows.size() >= lim) {
          break;
        }
      }
    }

    int fail = 0;
    int success = 0;
    for (Map<String, Object> r : rows) {
      String st = String.valueOf(r.get("completionStatus"));
      if ("Error".equalsIgnoreCase(st) || "Terminated".equalsIgnoreCase(st)) {
        fail++;
      } else if ("Success".equalsIgnoreCase(st)) {
        success++;
      }
    }

    Map<String, Object> data = new LinkedHashMap<>();
    data.put("tasks", rows);
    data.put("count", rows.size());
    data.put("successCount", success);
    data.put("failCount", fail);
    data.put(
        "canonicalOrder",
        Arrays.asList(
            "Aggregate MNB-HR",
            "Aggregate MNB-IT-Access",
            "Aggregate MNB-ActiveDirectory",
            "Aggregate MNB-CoreBanking",
            "Aggregate MNB-SAP-Finance",
            "Aggregate MNB-AWS-Cloud",
            "Aggregate MNB-WirePortal",
            "Refresh Identity Cube / Refresh MNB Identities"));
    data.put(
        "stopGo",
        "HR Aggregate FAIL → STOP pipeline. Target FAIL → ticket + continue. Refresh after targets.");
    return MnbAgentSupport.ok("UIAPI-61", data);
  }

  @GET
  @Path("inbox")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> inbox(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-62");
    int lim = limit == null ? 75 : Math.max(1, Math.min(limit, 200));
    QueryOptions qo = new QueryOptions();
    qo.addOrdering("created", false);
    qo.setResultLimit(lim);
    List<WorkItem> items = getContext().getObjects(WorkItem.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (items != null) {
      for (WorkItem wi : items) {
        if (wi == null) {
          continue;
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", wi.getId());
        row.put("name", wi.getName());
        row.put("description", wi.getDescription());
        row.put("type", wi.getType() != null ? wi.getType().name() : null);
        row.put("state", wi.getState() != null ? wi.getState().name() : null);
        row.put("owner", wi.getOwner() != null ? wi.getOwner().getName() : null);
        row.put(
            "ownerDisplay",
            wi.getOwner() != null ? wi.getOwner().getDisplayableName() : null);
        row.put("requester", wi.getRequester() != null ? wi.getRequester().getName() : null);
        row.put("created", wi.getCreated());
        row.put("modified", wi.getModified());
        rows.add(row);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("items", rows);
    data.put("count", rows.size());
    return MnbAgentSupport.ok("UIAPI-62", data);
  }

  @GET
  @Path("catalog")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> catalog(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-63");
    int lim = limit == null ? 100 : Math.max(1, Math.min(limit, 300));
    SailPointContext ctx = getContext();

    List<Map<String, Object>> roles = new ArrayList<>();
    QueryOptions rqo = new QueryOptions();
    rqo.setResultLimit(lim);
    List<Bundle> bundles = ctx.getObjects(Bundle.class, rqo);
    if (bundles != null) {
      for (Bundle b : bundles) {
        if (b == null) {
          continue;
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("name", b.getName());
        row.put("displayName", b.getDisplayableName());
        row.put("type", b.getType());
        Object attrReq = b.getAttribute("requestable");
        boolean requestable =
            attrReq == null
                || Boolean.TRUE.equals(attrReq)
                || "true".equalsIgnoreCase(String.valueOf(attrReq));
        row.put("requestable", requestable);
        row.put("disabled", Boolean.TRUE.equals(b.getAttribute("disabled")));
        roles.add(row);
      }
    }

    List<Map<String, Object>> ents = new ArrayList<>();
    QueryOptions eqo = new QueryOptions();
    eqo.setResultLimit(lim);
    List<ManagedAttribute> mas = ctx.getObjects(ManagedAttribute.class, eqo);
    if (mas != null) {
      for (ManagedAttribute ma : mas) {
        if (ma == null) {
          continue;
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("value", ma.getValue());
        row.put("displayName", ma.getDisplayableName());
        row.put("application", ma.getApplication() != null ? ma.getApplication().getName() : null);
        row.put("type", ma.getType());
        row.put("requestable", ma.isRequestable());
        row.put("privileged", isPrivilegedValue(ma.getValue()));
        ents.add(row);
      }
    }

    Map<String, Object> data = new LinkedHashMap<>();
    data.put("roles", roles);
    data.put("roleCount", roles.size());
    data.put("entitlements", ents);
    data.put("entitlementCount", ents.size());
    return MnbAgentSupport.ok("UIAPI-63", data);
  }

  @GET
  @Path("certs")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> certs(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-64");
    int lim = limit == null ? 50 : Math.max(1, Math.min(limit, 100));
    QueryOptions qo = new QueryOptions();
    qo.addOrdering("created", false);
    qo.setResultLimit(lim);
    List<Certification> certs = getContext().getObjects(Certification.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    if (certs != null) {
      for (Certification c : certs) {
        if (c == null) {
          continue;
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", c.getId());
        row.put("name", c.getName());
        row.put("type", c.getType() != null ? c.getType().name() : null);
        row.put("phase", c.getPhase() != null ? c.getPhase().name() : null);
        row.put(
            "certificationGroups",
            c.getCertificationGroups() != null ? c.getCertificationGroups().size() : 0);
        row.put("signed", c.getSigned());
        row.put("finished", c.getFinished());
        row.put("created", c.getCreated());
        row.put(
            "certifier",
            c.getCertifiers() != null && !c.getCertifiers().isEmpty()
                ? String.valueOf(c.getCertifiers().get(0))
                : null);
        rows.add(row);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("campaigns", rows);
    data.put("count", rows.size());
    data.put(
        "guidance",
        "Open a campaign below to decide items and sign. Mutate requires mutateGovernanceEnabled.");
    return MnbAgentSupport.ok("UIAPI-64", data);
  }

  @GET
  @Path("certs/{id}")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> certDetail(
      @PathParam("id") String id, @QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-64");
    int lim = limit == null ? 100 : Math.max(1, Math.min(limit, 300));
    SailPointContext ctx = getContext();
    Certification cert = MnbAgentSupport.requireByIdOrName(ctx, Certification.class, id, "UIAPI-64");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", cert.getId());
    data.put("name", cert.getName());
    data.put("type", cert.getType() != null ? cert.getType().name() : null);
    data.put("phase", cert.getPhase() != null ? cert.getPhase().name() : null);
    data.put("signed", cert.getSigned());
    data.put("finished", cert.getFinished());
    data.put("certifiers", cert.getCertifiers());

    List<Map<String, Object>> items = new ArrayList<>();
    List<CertificationEntity> entities = cert.getEntities();
    int undecided = 0;
    if (entities != null) {
      for (CertificationEntity ent : entities) {
        if (ent == null || ent.getItems() == null) {
          continue;
        }
        String identityName = ent.getIdentity();
        for (CertificationItem item : ent.getItems()) {
          if (item == null) {
            continue;
          }
          Map<String, Object> row = new LinkedHashMap<>();
          row.put("id", item.getId());
          row.put("identity", identityName);
          row.put("type", item.getType() != null ? item.getType().name() : null);
          row.put("bundle", item.getBundle());
          row.put(
              "applications",
              item.getApplicationNames() != null ? item.getApplicationNames() : Collections.emptyList());
          row.put(
              "summaryStatus",
              item.getSummaryStatus() != null ? item.getSummaryStatus().name() : null);
          CertificationAction action = item.getAction();
          String decision = null;
          if (action != null && action.getStatus() != null) {
            decision = action.getStatus().name();
          }
          row.put("decision", decision);
          if (decision == null
              || "Open".equalsIgnoreCase(decision)
              || "Waiting".equalsIgnoreCase(String.valueOf(item.getSummaryStatus()))) {
            undecided++;
          }
          items.add(row);
          if (items.size() >= lim) {
            break;
          }
        }
        if (items.size() >= lim) {
          break;
        }
      }
    }
    data.put("items", items);
    data.put("itemCount", items.size());
    data.put("undecidedCount", undecided);
    data.put(
        "guidance",
        "Decide each item (approve|revoke|mitigate|acknowledge) then Sign the campaign.");
    return MnbAgentSupport.ok("UIAPI-64", data);
  }

  @GET
  @Path("sod")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> sod(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-65");
    int lim = limit == null ? 100 : Math.max(1, Math.min(limit, 300));
    SailPointContext ctx = getContext();
    QueryOptions openQo = new QueryOptions();
    openQo.addFilter(Filter.eq("status", PolicyViolation.Status.Open));
    int openCount = ctx.countObjects(PolicyViolation.class, openQo);
    QueryOptions qo = new QueryOptions();
    qo.addFilter(Filter.eq("status", PolicyViolation.Status.Open));
    qo.addOrdering("created", false);
    qo.setResultLimit(lim);
    List<PolicyViolation> list = ctx.getObjects(PolicyViolation.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    Map<String, Integer> byPolicy = new LinkedHashMap<>();
    if (list != null) {
      for (PolicyViolation v : list) {
        if (v == null) {
          continue;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", v.getId());
        m.put("policyName", v.getPolicyName());
        m.put("constraintName", v.getConstraintName());
        Identity idn = v.getIdentity();
        m.put("identity", idn != null ? idn.getName() : null);
        m.put("identityDisplay", idn != null ? idn.getDisplayableName() : null);
        m.put("status", v.getStatus() != null ? v.getStatus().name() : null);
        m.put("created", v.getCreated());
        m.put("description", v.getDescription());
        rows.add(m);
        String pn = v.getPolicyName() != null ? v.getPolicyName() : "(unnamed)";
        byPolicy.put(pn, byPolicy.getOrDefault(pn, 0) + 1);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("openCount", openCount);
    data.put("violations", rows);
    data.put("count", rows.size());
    data.put("byPolicy", byPolicy);
    data.put("guidance", "Mitigate with comment for exam evidence; revoke conflicting access via Teller when needed.");
    return MnbAgentSupport.ok("UIAPI-65", data);
  }

  @GET
  @Path("identity360")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> identity360(@QueryParam("q") String q) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-66");
    if (Util.isNullOrEmpty(q) || q.trim().length() < 2) {
      throw MnbAgentSupport.error(
          400, "invalid_request", "q required (identity name, email, or display)", "UIAPI-66", null);
    }
    SailPointContext ctx = getContext();
    Identity idn;
    try {
      idn = MnbAgentSupport.resolveIdentity(ctx, q.trim(), "UIAPI-66");
    } catch (Exception first) {
      QueryOptions qo = new QueryOptions();
      String needle = q.trim().toLowerCase(Locale.ROOT);
      qo.addFilter(
          Filter.or(
              Filter.like("name", needle, Filter.MatchMode.ANYWHERE),
              Filter.like("displayName", needle, Filter.MatchMode.ANYWHERE),
              Filter.like("email", needle, Filter.MatchMode.ANYWHERE)));
      qo.setResultLimit(5);
      List<Identity> hits = ctx.getObjects(Identity.class, qo);
      if (hits == null || hits.isEmpty()) {
        throw MnbAgentSupport.error(404, "not_found", "Identity not found: " + q, "UIAPI-66", null);
      }
      idn = hits.get(0);
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("id", idn.getId());
    data.put("name", idn.getName());
    data.put("displayName", idn.getDisplayableName());
    data.put("email", idn.getEmail());
    data.put("inactive", idn.isInactive());
    data.put("firstname", idn.getFirstname());
    data.put("lastname", idn.getLastname());
    Identity mgr = idn.getManager();
    data.put("manager", mgr != null ? mgr.getName() : null);
    data.put("managerDisplay", mgr != null ? mgr.getDisplayableName() : null);
    data.put("title", attrStr(idn, "title", "jobTitle"));
    data.put("department", attrStr(idn, "departmentName", "department"));
    data.put("jobCode", attrStr(idn, "jobCode"));
    data.put("employeeType", attrStr(idn, "employeeType", "type"));
    data.put("location", attrStr(idn, "locationCode", "location"));
    data.put("userId", attrStr(idn, "userId", "employeeId"));
    data.put("startDate", attrStr(idn, "startDate", "hireDate"));
    data.put("endDate", attrStr(idn, "endDate", "terminationDate"));
    data.put("apps", linkAppNames(idn));

    List<Map<String, Object>> accounts = new ArrayList<>();
    if (idn.getLinks() != null) {
      for (Object o : idn.getLinks()) {
        if (!(o instanceof Link)) {
          continue;
        }
        Link link = (Link) o;
        Map<String, Object> a = new LinkedHashMap<>();
        Application app = link.getApplication();
        a.put("application", app != null ? app.getName() : null);
        a.put("nativeIdentity", link.getNativeIdentity());
        a.put("displayName", link.getDisplayName());
        a.put("disabled", link.isDisabled());
        a.put("privileged", isPrivilegedLink(link));
        accounts.add(a);
      }
    }
    data.put("accounts", accounts);

    List<String> roles = new ArrayList<>();
    if (idn.getAssignedRoles() != null) {
      for (Object o : idn.getAssignedRoles()) {
        if (o instanceof Bundle) {
          roles.add(((Bundle) o).getName());
        }
      }
    }
    data.put("assignedRoles", roles);
    List<String> detected = new ArrayList<>();
    if (idn.getDetectedRoles() != null) {
      for (Object o : idn.getDetectedRoles()) {
        if (o instanceof Bundle) {
          detected.add(((Bundle) o).getName());
        }
      }
    }
    data.put("detectedRoles", detected);

    List<String> caps = new ArrayList<>();
    if (idn.getCapabilities() != null) {
      for (Object o : idn.getCapabilities()) {
        if (o instanceof Capability) {
          caps.add(((Capability) o).getName());
        }
      }
    }
    data.put("capabilities", caps);

    List<String> wgs = new ArrayList<>();
    if (idn.getWorkgroups() != null) {
      for (Object o : idn.getWorkgroups()) {
        if (o instanceof Identity) {
          wgs.add(((Identity) o).getName());
        }
      }
    }
    data.put("workgroups", wgs);

    QueryOptions vqo = new QueryOptions();
    vqo.addFilter(Filter.eq("identity", idn));
    vqo.addFilter(Filter.eq("status", PolicyViolation.Status.Open));
    vqo.setResultLimit(20);
    List<PolicyViolation> viols = ctx.getObjects(PolicyViolation.class, vqo);
    List<Map<String, Object>> sod = new ArrayList<>();
    if (viols != null) {
      for (PolicyViolation v : viols) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", v.getId());
        m.put("policyName", v.getPolicyName());
        m.put("constraintName", v.getConstraintName());
        sod.add(m);
      }
    }
    data.put("openSod", sod);
    data.put("openSodCount", sod.size());
    return MnbAgentSupport.ok("UIAPI-66", data);
  }

  @GET
  @Path("jml")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> jmlTimeline(@QueryParam("identity") String identity)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-67");
    SailPointContext ctx = getContext();
    List<Map<String, Object>> personas = new ArrayList<>();
    // Seeded Meridian JML lab personas (stable keys)
    String[][] seeds =
        new String[][] {
          {"MNB00120", "joiner", "Nina Joiner — recent hire birthright path"},
          {"MNB00090", "mover", "Priya — commercial banking move / leftover wire risk"},
          {"MNB00092", "leaver", "Jordan Reed — termination residual access hunt"},
          {"MNB00095", "loa", "Sofia — leave of absence hygiene"},
          {"MNB00094", "rehire", "Samir Hassan — reinstate / rehire access"},
          {"MNB00093", "contractor-end", "Raj External — contractor end + AWS risk"},
        };
    for (String[] seed : seeds) {
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("identityKey", seed[0]);
      row.put("eventType", seed[1]);
      row.put("narrative", seed[2]);
      Identity idn = ctx.getObjectByName(Identity.class, seed[0]);
      if (idn != null) {
        row.put("found", true);
        row.put("displayName", idn.getDisplayableName());
        row.put("inactive", idn.isInactive());
        row.put("manager", idn.getManager() != null ? idn.getManager().getName() : null);
        row.put("department", attrStr(idn, "departmentName", "department"));
        row.put("accountCount", idn.getLinks() != null ? idn.getLinks().size() : 0);
        row.put("apps", linkAppNames(idn));
        List<Map<String, Object>> events = new ArrayList<>();
        events.add(jmlEvent("HR attribute snapshot", attrStr(idn, "employeeType", "type"), idn.getCreated()));
        if (!Util.isNullOrEmpty(attrStr(idn, "startDate", "hireDate"))) {
          events.add(jmlEvent("Hire / start", attrStr(idn, "startDate", "hireDate"), null));
        }
        if (!Util.isNullOrEmpty(attrStr(idn, "endDate", "terminationDate"))) {
          events.add(jmlEvent("End / terminate", attrStr(idn, "endDate", "terminationDate"), null));
        }
        if (idn.isInactive()) {
          events.add(jmlEvent("Cube inactive", "true", idn.getModified()));
        }
        row.put("timeline", events);
      } else {
        row.put("found", false);
        row.put("timeline", Arrays.asList(jmlEvent("Not in IIQ yet", seed[0], null)));
      }
      if (!Util.isNullOrEmpty(identity)
          && !seed[0].equalsIgnoreCase(identity)
          && (idn == null
              || idn.getDisplayableName() == null
              || !idn.getDisplayableName().toLowerCase(Locale.ROOT).contains(identity.toLowerCase(Locale.ROOT)))) {
        continue;
      }
      personas.add(row);
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("personas", personas);
    data.put("count", personas.size());
    data.put(
        "guidance",
        "Timeline is inferred from cube attrs + lab narrative. Launch JML via toolkit POST /agent/jml/{event}.");
    return MnbAgentSupport.ok("UIAPI-67", data);
  }

  @GET
  @Path("evidence")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> evidence(
      @QueryParam("identity") String identity, @QueryParam("limit") Integer limit)
      throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-68");
    int lim = limit == null ? 40 : Math.max(1, Math.min(limit, 200));
    SailPointContext ctx = getContext();
    Map<String, Object> pack = new LinkedHashMap<>();
    pack.put("bank", "MNB");
    pack.put("generatedAt", new Date().toString());
    pack.put("title", "Meridian exam evidence pack");

    if (!Util.isNullOrEmpty(identity)) {
      @SuppressWarnings("unchecked")
      Map<String, Object> cube = (Map<String, Object>) identity360(identity).get("data");
      pack.put("identity", cube);
    }

    QueryOptions aqo = new QueryOptions();
    aqo.addOrdering("created", false);
    aqo.setResultLimit(lim);
    List<AuditEvent> events = ctx.getObjects(AuditEvent.class, aqo);
    List<Map<String, Object>> auditRows = new ArrayList<>();
    if (events != null) {
      for (AuditEvent e : events) {
        if (e == null) {
          continue;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("action", e.getAction());
        m.put("source", e.getSource());
        m.put("target", e.getTarget());
        m.put("created", e.getCreated());
        auditRows.add(m);
      }
    }
    pack.put("recentAudit", auditRows);

    @SuppressWarnings("unchecked")
    Map<String, Object> sodData = (Map<String, Object>) sod(Math.min(lim, 50)).get("data");
    pack.put("sodOpenCount", sodData != null ? sodData.get("openCount") : 0);
    pack.put("sodSample", sodData != null ? sodData.get("violations") : Collections.emptyList());

    @SuppressWarnings("unchecked")
    Map<String, Object> certData = (Map<String, Object>) certs(Math.min(lim, 20)).get("data");
    pack.put("certCampaigns", certData != null ? certData.get("campaigns") : Collections.emptyList());

    pack.put(
        "checklist",
        Arrays.asList(
            "Manager hierarchy reconciled (org chart / managersAssociateID)",
            "No login-named orphan cubes; create-identities OFF on targets",
            "Open SoD violations mitigated or remediated with comments",
            "Certification campaigns signed for in-scope populations",
            "Leaver residual accounts disabled or ticketed"));
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("pack", pack);
    data.put("downloadHint", "Copy JSON or use browser Download on Evidence desk");
    return MnbAgentSupport.ok("UIAPI-68", data);
  }

  @GET
  @Path("provisioning")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> provisioning(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-69");
    int lim = limit == null ? 50 : Math.max(1, Math.min(limit, 200));
    QueryOptions qo = new QueryOptions();
    qo.addOrdering("created", false);
    qo.setResultLimit(lim);
    List<ProvisioningTransaction> txs =
        getContext().getObjects(ProvisioningTransaction.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    int fail = 0;
    if (txs != null) {
      for (ProvisioningTransaction t : txs) {
        if (t == null) {
          continue;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", t.getId());
        m.put("name", t.getName());
        m.put("application", t.getApplicationName());
        m.put("identity", t.getIdentityName());
        m.put("identityDisplay", t.getIdentityDisplayName());
        m.put("operation", t.getOperation());
        m.put(
            "status",
            t.getStatus() != null ? t.getStatus().name() : null);
        m.put("type", t.getType() != null ? t.getType().name() : null);
        m.put("created", t.getCreated());
        String st = t.getStatus() != null ? t.getStatus().name() : "";
        if (st.toLowerCase(Locale.ROOT).contains("fail")
            || st.toLowerCase(Locale.ROOT).contains("error")) {
          fail++;
        }
        rows.add(m);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("transactions", rows);
    data.put("count", rows.size());
    data.put("failCount", fail);
    data.put(
        "guidance",
        "Retry failed plans via toolkit POST /agent/provisioning/{id}/retry or Admin Console.");
    return MnbAgentSupport.ok("UIAPI-69", data);
  }

  @GET
  @Path("workgroups")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> workgroups(
      @QueryParam("name") String name, @QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-70");
    int lim = limit == null ? 50 : Math.max(1, Math.min(limit, 200));
    SailPointContext ctx = getContext();
    QueryOptions gqo = new QueryOptions();
    gqo.addFilter(Filter.eq("workgroup", true));
    gqo.setResultLimit(lim);
    List<Identity> groups = ctx.getObjects(Identity.class, gqo);
    // Preload people for membership scan (lab scale)
    QueryOptions pqo = new QueryOptions();
    pqo.setResultLimit(5000);
    List<Identity> people = ctx.getObjects(Identity.class, pqo);

    List<Map<String, Object>> rows = new ArrayList<>();
    if (groups != null) {
      for (Identity g : groups) {
        if (g == null) {
          continue;
        }
        if (!Util.isNullOrEmpty(name) && !g.getName().equalsIgnoreCase(name)) {
          continue;
        }
        List<Map<String, Object>> members = new ArrayList<>();
        if (people != null) {
          for (Identity p : people) {
            if (p == null || p.isWorkgroup()) {
              continue;
            }
            try {
              if (p.isInWorkGroup(g)) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("name", p.getName());
                m.put("displayName", p.getDisplayableName());
                m.put("email", p.getEmail());
                members.add(m);
              }
            } catch (Exception ignore) {
              // ignore membership probe failures
            }
          }
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("name", g.getName());
        row.put("displayName", g.getDisplayableName());
        row.put("id", g.getId());
        row.put("memberCount", members.size());
        row.put("members", members);
        List<String> caps = new ArrayList<>();
        if (g.getCapabilities() != null) {
          for (Object o : g.getCapabilities()) {
            if (o instanceof Capability) {
              caps.add(((Capability) o).getName());
            }
          }
        }
        row.put("capabilities", caps);
        rows.add(row);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("workgroups", rows);
    data.put("count", rows.size());
    return MnbAgentSupport.ok("UIAPI-70", data);
  }

  @GET
  @Path("heatmap")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> heatmap(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-71");
    int lim = limit == null ? 150 : Math.max(1, Math.min(limit, 400));
    QueryOptions eqo = new QueryOptions();
    eqo.setResultLimit(lim);
    List<ManagedAttribute> mas = getContext().getObjects(ManagedAttribute.class, eqo);
    Map<String, Integer> privByApp = new LinkedHashMap<>();
    Map<String, Integer> totalByApp = new LinkedHashMap<>();
    List<Map<String, Object>> hot = new ArrayList<>();
    if (mas != null) {
      for (ManagedAttribute ma : mas) {
        if (ma == null) {
          continue;
        }
        String app = ma.getApplication() != null ? ma.getApplication().getName() : "(none)";
        totalByApp.put(app, totalByApp.getOrDefault(app, 0) + 1);
        boolean priv = isPrivilegedValue(ma.getValue());
        if (priv) {
          privByApp.put(app, privByApp.getOrDefault(app, 0) + 1);
          Map<String, Object> row = new LinkedHashMap<>();
          row.put("application", app);
          row.put("value", ma.getValue());
          row.put("displayName", ma.getDisplayableName());
          row.put("requestable", ma.isRequestable());
          hot.add(row);
        }
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("privilegedByApp", privByApp);
    data.put("totalByApp", totalByApp);
    data.put("hotEntitlements", hot);
    data.put("hotCount", hot.size());
    data.put("guidance", "Use with certs + AR catalog — privileged requestable items need dual control.");
    return MnbAgentSupport.ok("UIAPI-71", data);
  }

  @GET
  @Path("audit")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> audit(@QueryParam("limit") Integer limit) throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-72");
    int lim = limit == null ? 75 : Math.max(1, Math.min(limit, 300));
    QueryOptions qo = new QueryOptions();
    qo.addOrdering("created", false);
    qo.setResultLimit(lim);
    List<AuditEvent> events = getContext().getObjects(AuditEvent.class, qo);
    List<Map<String, Object>> rows = new ArrayList<>();
    Map<String, Integer> byAction = new LinkedHashMap<>();
    if (events != null) {
      for (AuditEvent e : events) {
        if (e == null) {
          continue;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", e.getId());
        m.put("action", e.getAction());
        m.put("source", e.getSource());
        m.put("target", e.getTarget());
        m.put("created", e.getCreated());
        rows.add(m);
        String a = e.getAction() != null ? e.getAction() : "(none)";
        byAction.put(a, byAction.getOrDefault(a, 0) + 1);
      }
    }
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("events", rows);
    data.put("count", rows.size());
    data.put("byAction", byAction);
    return MnbAgentSupport.ok("UIAPI-72", data);
  }

  @GET
  @Path("menu")
  @Produces(MediaType.APPLICATION_JSON)
  public Map<String, Object> menu() throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-60");
    List<Map<String, Object>> groups = new ArrayList<>();
    groups.add(
        menuGroup(
            "ops",
            "Ops",
            "Nightly health & remediation",
            menuItem("hub", "Command hub", "Counts across every desk"),
            menuItem("orphans", "Orphan desk", "Merge login-named cubes & correlate links"),
            menuItem("ops", "Aggregation pipeline", "Stop/go board for agg + refresh"),
            menuItem("provisioning", "Provisioning debugger", "Failed plans & retries")));
    groups.add(
        menuGroup(
            "business",
            "Business",
            "Approvers, requesters, managers",
            menuItem("inbox", "Approval inbox", "Work items decide"),
            menuItem("catalog", "Access catalog", "Roles & entitlements"),
            menuItem("certs", "Cert console", "Campaign coach"),
            menuItem("orgchart", "Org chart", "Hierarchy + risk badges", "/orgchart.html")));
    groups.add(
        menuGroup(
            "control",
            "Control room",
            "Bank-grade governance",
            menuItem("sod", "SoD war room", "Open violations triage"),
            menuItem("identity", "Identity 360", "Helpdesk workbench"),
            menuItem("jml", "JML timeline", "Joiner/mover/leaver personas"),
            menuItem("evidence", "Evidence pack", "Exam-ready JSON binder")));
    groups.add(
        menuGroup(
            "explore",
            "Explore",
            "Deep dives",
            menuItem("heatmap", "Risk heatmap", "Privileged entitlements by app"),
            menuItem("workgroups", "Workgroups", "Membership + capabilities"),
            menuItem("audit", "Audit activity", "Recent AuditEvent stream"),
            menuItem("teller", "Teller chat", "NL agent over MCP", "/")));
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("groups", groups);
    data.put("version", MnbToolkitPingResource.PLUGIN_VERSION);
    return MnbAgentSupport.ok("UIAPI-60", data);
  }

  @GET
  @Path("summary")
  @Produces(MediaType.APPLICATION_JSON)
  @SuppressWarnings("unchecked")
  public Map<String, Object> summary() throws GeneralException {
    MnbAgentSupport.requireAgentEnabled(this, "UIAPI-60");
    Map<String, Object> orphans = (Map<String, Object>) orphans(50).get("data");
    Map<String, Object> pipe = (Map<String, Object>) pipeline(20).get("data");
    Map<String, Object> inboxData = (Map<String, Object>) inbox(50).get("data");
    Map<String, Object> certData = (Map<String, Object>) certs(20).get("data");
    Map<String, Object> sodData = (Map<String, Object>) sod(20).get("data");
    Map<String, Object> provData = (Map<String, Object>) provisioning(30).get("data");
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("loginNamedCount", orphans != null ? orphans.get("loginNamedCount") : 0);
    data.put("uncorrelatedCount", orphans != null ? orphans.get("uncorrelatedCount") : 0);
    data.put("pipelineFailCount", pipe != null ? pipe.get("failCount") : 0);
    data.put("inboxCount", inboxData != null ? inboxData.get("count") : 0);
    data.put("certCount", certData != null ? certData.get("count") : 0);
    data.put("sodOpenCount", sodData != null ? sodData.get("openCount") : 0);
    data.put("provFailCount", provData != null ? provData.get("failCount") : 0);
    return MnbAgentSupport.ok("UIAPI-60", data);
  }

  private static Map<String, Object> menuGroup(
      String id, String title, String subtitle, Map<String, Object>... items) {
    Map<String, Object> g = new LinkedHashMap<>();
    g.put("id", id);
    g.put("title", title);
    g.put("subtitle", subtitle);
    g.put("items", Arrays.asList(items));
    return g;
  }

  private static Map<String, Object> menuItem(String id, String title, String blurb) {
    return menuItem(id, title, blurb, null);
  }

  private static Map<String, Object> menuItem(String id, String title, String blurb, String href) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("id", id);
    m.put("title", title);
    m.put("blurb", blurb);
    if (href != null) {
      m.put("href", href);
    }
    return m;
  }

  private static Map<String, Object> jmlEvent(String label, String detail, Date when) {
    Map<String, Object> e = new LinkedHashMap<>();
    e.put("label", label);
    e.put("detail", detail);
    e.put("when", when);
    return e;
  }

  private static String attrStr(Identity idn, String... keys) {
    if (idn == null || keys == null) {
      return null;
    }
    for (String k : keys) {
      Object v = idn.getAttribute(k);
      if (v != null && !Util.isNullOrEmpty(String.valueOf(v))) {
        return String.valueOf(v);
      }
    }
    return null;
  }

  private static boolean emailsMatch(Identity a, Identity b) {
    if (a == null || b == null || Util.isNullOrEmpty(a.getEmail()) || Util.isNullOrEmpty(b.getEmail())) {
      return false;
    }
    return a.getEmail().equalsIgnoreCase(b.getEmail());
  }

  private static List<String> linkAppNames(Identity idn) {
    List<String> apps = new ArrayList<>();
    if (idn.getLinks() == null) {
      return apps;
    }
    Set<String> seen = new HashSet<>();
    for (Object o : idn.getLinks()) {
      if (o instanceof Link) {
        Link l = (Link) o;
        Application app = l.getApplication();
        if (app != null && seen.add(app.getName())) {
          apps.add(app.getName());
        }
      }
    }
    return apps;
  }

  private static boolean isPrivilegedLink(Link link) {
    if (link == null) {
      return false;
    }
    for (String key : new String[] {"entitlement", "itAccess", "groups", "memberOf"}) {
      Object v = link.getAttribute(key);
      if (v != null && isPrivilegedValue(String.valueOf(v))) {
        return true;
      }
    }
    return false;
  }

  private static boolean isPrivilegedValue(String v) {
    if (v == null) {
      return false;
    }
    String u = v.toUpperCase(Locale.ROOT);
    for (String p : PRIVILEGED) {
      if (u.contains(p)) {
        return true;
      }
    }
    return false;
  }
}
