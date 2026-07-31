package com.meridianbank.iiq.plugin.rest;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javax.ws.rs.WebApplicationException;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

import sailpoint.api.SailPointContext;
import sailpoint.object.Filter;
import sailpoint.object.QueryOptions;
import sailpoint.object.SailPointObject;
import sailpoint.tools.GeneralException;
import sailpoint.tools.Util;

/** Shared helpers for Meridian agent orchestration resources. */
public final class MnbAgentSupport {

  private MnbAgentSupport() {}

  public static Map<String, Object> ok(String gapId, Object data) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("status", "ok");
    body.put("gapId", gapId);
    body.put("bank", MnbToolkitPingResource.BANK_CODE);
    body.put("plugin", MnbToolkitPingResource.PLUGIN_NAME);
    body.put("data", data);
    return body;
  }

  public static WebApplicationException error(int status, String code, String detail, String gapId, String guidance) {
    Map<String, Object> err = new LinkedHashMap<>();
    err.put("error", code);
    err.put("detail", detail);
    err.put("status", status);
    err.put("gapId", gapId);
    if (guidance != null) {
      err.put("guidance", guidance);
    }
    return new WebApplicationException(
        Response.status(status).entity(err).type(MediaType.APPLICATION_JSON).build());
  }

  public static boolean flag(sailpoint.rest.plugin.BasePluginResource res, String key) {
    try {
      String v = res.getSettingString(key);
      return v != null && ("true".equalsIgnoreCase(v.trim()) || "1".equals(v.trim()));
    } catch (Exception e) {
      return false;
    }
  }

  public static void requireAgentEnabled(sailpoint.rest.plugin.BasePluginResource res, String gapId) {
    if (!flag(res, "agentApiEnabled")) {
      throw error(
          403,
          "agent_api_disabled",
          "agentApiEnabled=false",
          gapId,
          "Enable plugin setting agentApiEnabled=true");
    }
  }

  public static void requireMutateGov(sailpoint.rest.plugin.BasePluginResource res, String gapId) {
    requireAgentEnabled(res, gapId);
    if (!flag(res, "mutateGovernanceEnabled")) {
      throw error(
          403,
          "mutate_governance_disabled",
          "mutateGovernanceEnabled=false",
          gapId,
          "Enable mutateGovernanceEnabled for cert/SoD/work-item mutate APIs");
    }
  }

  public static void requirePasswordMutate(sailpoint.rest.plugin.BasePluginResource res, String gapId) {
    requireAgentEnabled(res, gapId);
    if (!flag(res, "passwordResetEnabled")) {
      throw error(
          403,
          "password_reset_disabled",
          "passwordResetEnabled=false",
          gapId,
          "Enable passwordResetEnabled for admin password/unlock APIs");
    }
  }

  public static void requireAdvancedOps(sailpoint.rest.plugin.BasePluginResource res, String gapId) {
    requireAgentEnabled(res, gapId);
    if (!flag(res, "advancedOpsEnabled")) {
      throw error(
          403,
          "advanced_ops_disabled",
          "advancedOpsEnabled=false",
          gapId,
          "Enable advancedOpsEnabled for app config mutate, system config, object import, plugin enable/install");
    }
  }

  public static String str(Object o) {
    return o == null ? null : String.valueOf(o).trim();
  }

  public static Map<String, Object> bodyOrEmpty(Map<String, Object> body) {
    return body == null ? new LinkedHashMap<>() : body;
  }

  public static <T extends SailPointObject> List<Map<String, Object>> listSummaries(
      SailPointContext ctx, Class<T> type, int limit) throws GeneralException {
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(Math.max(1, Math.min(limit, 500)));
    List<T> objs = ctx.getObjects(type, qo);
    List<Map<String, Object>> out = new ArrayList<>();
    if (objs == null) {
      return out;
    }
    for (T o : objs) {
      Map<String, Object> m = new LinkedHashMap<>();
      m.put("id", o.getId());
      m.put("name", o.getName());
      out.add(m);
    }
    return out;
  }

  public static <T extends SailPointObject> T requireByIdOrName(
      SailPointContext ctx, Class<T> type, String idOrName, String gapId) throws GeneralException {
    if (Util.isNullOrEmpty(idOrName)) {
      throw error(400, "invalid_request", "id/name required", gapId, null);
    }
    T obj = ctx.getObjectById(type, idOrName);
    if (obj == null) {
      obj = ctx.getObjectByName(type, idOrName);
    }
    if (obj == null) {
      throw error(404, "not_found", type.getSimpleName() + " not found: " + idOrName, gapId, null);
    }
    return obj;
  }

  public static QueryOptions namePrefix(String prefix, int limit) {
    QueryOptions qo = new QueryOptions();
    qo.setResultLimit(Math.max(1, Math.min(limit, 500)));
    if (!Util.isNullOrEmpty(prefix)) {
      qo.addFilter(Filter.like("name", prefix, Filter.MatchMode.START));
    }
    return qo;
  }

  /** Resolve identity by name, id, or display-name → first.last lab convention. */
  public static sailpoint.object.Identity resolveIdentity(
      SailPointContext ctx, String hint, String gapId) throws GeneralException {
    if (Util.isNullOrEmpty(hint)) {
      throw error(400, "invalid_request", "identity required", gapId, null);
    }
    sailpoint.object.Identity id = ctx.getObjectByName(sailpoint.object.Identity.class, hint);
    if (id == null) {
      id = ctx.getObjectById(sailpoint.object.Identity.class, hint);
    }
    if (id == null && hint.contains(" ")) {
      String dotted = hint.trim().toLowerCase().replace(' ', '.');
      id = ctx.getObjectByName(sailpoint.object.Identity.class, dotted);
    }
    if (id == null) {
      throw error(404, "not_found", "Identity not found: " + hint, gapId, null);
    }
    return id;
  }

  public static String firstNonEmpty(String... vals) {
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
}
