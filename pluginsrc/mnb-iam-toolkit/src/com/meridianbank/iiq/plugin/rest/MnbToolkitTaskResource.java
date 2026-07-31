package com.meridianbank.iiq.plugin.rest;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import javax.ws.rs.Consumes;
import javax.ws.rs.GET;
import javax.ws.rs.NotFoundException;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.WebApplicationException;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

import org.apache.log4j.Logger;

import sailpoint.api.SailPointContext;
import sailpoint.api.TaskManager;
import sailpoint.object.TaskDefinition;
import sailpoint.object.TaskResult;
import sailpoint.rest.plugin.BasePluginResource;
import sailpoint.rest.plugin.RequiredRight;
import sailpoint.tools.GeneralException;
import sailpoint.tools.Message;
import sailpoint.tools.Util;

/**
 * Agent-oriented task launch API — closes UIAPI-01/02 for allowlisted TaskDefinitions.
 *
 * <p>{@code POST /identityiq/plugin/rest/mnbToolkit/tasks/run} launches a named IIQ task
 * (e.g. account aggregation / identity refresh) without the UI. Gated by
 * {@code MNBToolkitTaskRun}, plugin kill switch {@code taskRunEnabled}, and
 * {@code allowedTaskNames} allowlist.
 */
@Path("mnbToolkit/tasks")
@RequiredRight("MNBToolkitTaskRun")
public class MnbToolkitTaskResource extends BasePluginResource {

  private static final Logger log = Logger.getLogger(MnbToolkitTaskResource.class);

  public static final String PLUGIN_NAME = MnbToolkitPingResource.PLUGIN_NAME;
  private static final int MAX_SYNC_SECONDS = 120;

  @Override
  public String getPluginName() {
    return PLUGIN_NAME;
  }

  /**
   * List tasks currently permitted by the allowlist setting (does not dump all TaskDefinitions).
   */
  @GET
  @Path("allowed")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitTaskRun")
  public Map<String, Object> listAllowed() throws GeneralException {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("enabled", isTaskRunEnabled());
    body.put("allowedTaskNames", getAllowlist());
    body.put("bank", MnbToolkitPingResource.BANK_CODE);
    return body;
  }

  /**
   * Launch an allowlisted TaskDefinition.
   *
   * <p>Body example:
   * <pre>
   * {
   *   "taskName": "Account Aggregation Refresh",
   *   "sync": false,
   *   "args": { "applications": "MNB-Wire-Portal" }
   * }
   * </pre>
   */
  @POST
  @Path("run")
  @Consumes(MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitTaskRun")
  public Map<String, Object> run(Map<String, Object> request) throws GeneralException {
    if (!isTaskRunEnabled()) {
      throw conflict(403, "task_run_disabled", "taskRunEnabled=false (kill switch)");
    }
    if (request == null) {
      throw conflict(400, "invalid_request", "JSON body required");
    }
    String taskName = str(request.get("taskName"));
    if (Util.isNullOrEmpty(taskName)) {
      throw conflict(400, "invalid_request", "taskName is required");
    }
    assertAllowlisted(taskName);

    boolean sync = Boolean.TRUE.equals(request.get("sync")) || "true".equalsIgnoreCase(str(request.get("sync")));
    @SuppressWarnings("unchecked")
    Map<String, Object> args =
        request.get("args") instanceof Map ? new HashMap<>((Map<String, Object>) request.get("args")) : new HashMap<>();

    SailPointContext context = getContext();
    TaskManager tm = new TaskManager(context);
    TaskDefinition def = tm.getTaskDefinition(taskName);
    if (def == null) {
      throw new NotFoundException("TaskDefinition not found: " + taskName);
    }

    String launcher = context.getUserName();
    tm.setLauncher(launcher);
    log.warn(
        "MNB toolkit task launch requested taskName="
            + taskName
            + " sync="
            + sync
            + " launcher="
            + launcher
            + " argKeys="
            + args.keySet());

    TaskResult result;
    if (sync) {
      // Cap sync to avoid agent timeouts / holding HTTP threads on long aggregations.
      int waitHint = MAX_SYNC_SECONDS;
      Object waitObj = request.get("syncTimeoutSeconds");
      if (waitObj instanceof Number) {
        waitHint = Math.min(MAX_SYNC_SECONDS, Math.max(1, ((Number) waitObj).intValue()));
      }
      // runSync has no timeout param; document that agents should prefer sync=false for aggregations.
      if (waitHint < MAX_SYNC_SECONDS) {
        log.info("syncTimeoutSeconds ignored by TaskManager.runSync; prefer sync=false for long tasks");
      }
      result = tm.runSync(def, args);
    } else {
      result = tm.runWithResult(def, args);
    }
    context.commitTransaction();
    return toResultMap(result, taskName, sync, "accepted");
  }

  /**
   * Poll a TaskResult launched by this (or any) process — still requires MNBToolkitTaskRun.
   */
  @GET
  @Path("results/{id}")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitTaskRun")
  public Map<String, Object> getResult(@PathParam("id") String id) throws GeneralException {
    if (Util.isNullOrEmpty(id)) {
      throw conflict(400, "invalid_request", "id is required");
    }
    if (!isTaskRunEnabled()) {
      throw conflict(403, "task_run_disabled", "taskRunEnabled=false (kill switch)");
    }
    SailPointContext context = getContext();
    TaskResult result = context.getObjectById(TaskResult.class, id);
    if (result == null) {
      // allow lookup by name as fallback
      result = context.getObjectByName(TaskResult.class, id);
    }
    if (result == null) {
      throw new NotFoundException("TaskResult not found: " + id);
    }
    String taskName = result.getDefinition() != null ? result.getDefinition().getName() : result.getName();
    return toResultMap(result, taskName, null, "status");
  }

  private void assertAllowlisted(String taskName) {
    List<String> allowed = getAllowlist();
    if (allowed.isEmpty()) {
      throw conflict(
          403,
          "allowlist_empty",
          "allowedTaskNames is empty — configure plugin setting before launching tasks");
    }
    for (String pattern : allowed) {
      if (matches(pattern, taskName)) {
        return;
      }
    }
    throw conflict(403, "task_not_allowlisted", "taskName not in allowedTaskNames: " + taskName);
  }

  private static boolean matches(String pattern, String taskName) {
    if (pattern == null || pattern.isEmpty()) {
      return false;
    }
    if (pattern.endsWith("*")) {
      String prefix = pattern.substring(0, pattern.length() - 1);
      return taskName.regionMatches(true, 0, prefix, 0, prefix.length());
    }
    return pattern.equalsIgnoreCase(taskName);
  }

  private boolean isTaskRunEnabled() {
    try {
      String v = getSettingString("taskRunEnabled");
      return v != null && ("true".equalsIgnoreCase(v.trim()) || "1".equals(v.trim()));
    } catch (Exception e) {
      return false;
    }
  }

  private List<String> getAllowlist() {
    try {
      String raw = getSettingString("allowedTaskNames");
      if (Util.isNullOrEmpty(raw)) {
        return Collections.emptyList();
      }
      return Arrays.stream(raw.split(","))
          .map(String::trim)
          .filter(s -> !s.isEmpty())
          .collect(Collectors.toList());
    } catch (Exception e) {
      return Collections.emptyList();
    }
  }

  private Map<String, Object> toResultMap(TaskResult result, String taskName, Boolean sync, String mode)
      throws GeneralException {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("status", result != null && result.isComplete() ? (result.isSuccess() ? "success" : "failed") : "running");
    body.put("mode", mode);
    body.put("taskName", taskName);
    if (sync != null) {
      body.put("sync", sync);
    }
    if (result != null) {
      body.put("taskResultId", result.getId());
      body.put("taskResultName", result.getName());
      body.put("complete", result.isComplete());
      body.put("success", result.isSuccess());
      body.put("percentComplete", result.getPercentComplete());
      body.put("progress", result.getProgress());
      body.put("launcher", result.getLauncher());
      body.put("launched", formatDate(result.getLaunched()));
      body.put("completed", formatDate(result.getCompleted()));
      if (result.getCompletionStatus() != null) {
        body.put("completionStatus", result.getCompletionStatus().name());
      }
      List<String> messages = new ArrayList<>();
      if (result.getMessages() != null) {
        for (Message m : result.getMessages()) {
          if (m != null) {
            messages.add(m.getMessage() != null ? m.getMessage() : m.toString());
          }
        }
      }
      body.put("messages", messages);
    }
    body.put("bank", MnbToolkitPingResource.BANK_CODE);
    body.put("plugin", PLUGIN_NAME);
    return body;
  }

  private static String formatDate(Date d) {
    return d == null ? null : d.toInstant().toString();
  }

  private static String str(Object o) {
    return o == null ? null : String.valueOf(o).trim();
  }

  private static WebApplicationException conflict(int status, String code, String detail) {
    Map<String, Object> err = new LinkedHashMap<>();
    err.put("error", code);
    err.put("detail", detail);
    err.put("status", status);
    return new WebApplicationException(
        Response.status(status).entity(err).type(MediaType.APPLICATION_JSON).build());
  }
}
