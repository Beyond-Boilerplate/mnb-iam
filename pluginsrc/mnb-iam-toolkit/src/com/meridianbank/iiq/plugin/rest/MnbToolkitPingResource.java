package com.meridianbank.iiq.plugin.rest;

import java.util.HashMap;
import java.util.Map;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;

import org.apache.log4j.Logger;

import sailpoint.rest.plugin.BasePluginResource;
import sailpoint.rest.plugin.RequiredRight;

/**
 * Meridian IAM Toolkit health ping — closes GAP-PLUGIN-001.
 *
 * <p>Contract: {@code GET /identityiq/plugin/rest/mnbToolkit/ping} returns JSON
 * with {@code status}/{@code bank=MNB}. Gated by right {@code MNBToolkitAccess}.
 */
@Path("mnbToolkit")
@RequiredRight("MNBToolkitAccess")
public class MnbToolkitPingResource extends BasePluginResource {

  private static final Logger log = Logger.getLogger(MnbToolkitPingResource.class);

  public static final String PLUGIN_NAME = "mnb_iam_toolkit";
  public static final String PLUGIN_VERSION = "1.3.15";
  public static final String BANK_CODE = "MNB";

  @Override
  public String getPluginName() {
    return PLUGIN_NAME;
  }

  /**
   * Synthetic health check for monitors and lab smoke tests.
   *
   * @return JSON map with status, bank, plugin, version, feature flags
   */
  @GET
  @Path("ping")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAccess")
  public Map<String, Object> ping() {
    Map<String, Object> body = new HashMap<>();
    body.put("status", "ok");
    body.put("bank", BANK_CODE);
    body.put("plugin", PLUGIN_NAME);
    body.put("version", PLUGIN_VERSION);
    String banner = null;
    try {
      banner = getSettingString("toolkitBanner");
    } catch (Exception e) {
      log.debug("toolkitBanner setting unavailable: " + e.getMessage());
    }
    if (banner != null && !banner.isEmpty()) {
      body.put("banner", banner);
    }
    Map<String, Object> flags = new HashMap<>();
    flags.put("agentApiEnabled", MnbAgentSupport.flag(this, "agentApiEnabled"));
    flags.put("taskRunEnabled", MnbAgentSupport.flag(this, "taskRunEnabled"));
    flags.put("mutateGovernanceEnabled", MnbAgentSupport.flag(this, "mutateGovernanceEnabled"));
    flags.put("passwordResetEnabled", MnbAgentSupport.flag(this, "passwordResetEnabled"));
    flags.put("advancedOpsEnabled", MnbAgentSupport.flag(this, "advancedOpsEnabled"));
    body.put("flags", flags);
    boolean ready =
        Boolean.TRUE.equals(flags.get("agentApiEnabled"))
            && Boolean.TRUE.equals(flags.get("taskRunEnabled"));
    body.put("agentReady", ready);
    if (!ready) {
      body.put(
          "guidance",
          "Enable plugin settings via POST /mnbToolkit/agent/plugins/mnb_iam_toolkit/settings "
              + "or UI → Plugins → Meridian Custom APIs");
    }
    return body;
  }
}
