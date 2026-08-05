package com.meridianbank.iiq.plugin.rest;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.MediaType;

import sailpoint.api.SailPointContext;
import sailpoint.object.Application;
import sailpoint.object.Identity;
import sailpoint.object.Link;
import sailpoint.object.Workflow;
import sailpoint.rest.plugin.BasePluginResource;
import sailpoint.rest.plugin.RequiredRight;
import sailpoint.tools.GeneralException;

/**
 * Enterprise Lab v2 helpers — pack presence and lightweight identity/JML status.
 */
@Path("mnbToolkit/enterprise")
@RequiredRight("MNBToolkitAgent")
public class MnbEnterpriseResource extends BasePluginResource {

  @Override
  public String getPluginName() {
    return "mnb_iam_toolkit";
  }

  @GET
  @Path("status")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> status() throws GeneralException {
    SailPointContext ctx = getContext();
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("pack", "enterprise-lab-v2");
    List<Map<String, Object>> apps = new ArrayList<>();
    for (String name :
        new String[] {
          "MNB-Workday",
          "MNB-ActiveDirectory-Live",
          "MNB-Okta",
          "MNB-CoreBanking",
          "MNB-Salesforce-CRM-Live",
          "MNB-ServiceNow",
          "MNB-OpenLDAP",
          "MNB-HR"
        }) {
      Application app = ctx.getObjectByName(Application.class, name);
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("name", name);
      row.put("present", app != null);
      if (app != null) {
        row.put("type", app.getType());
        row.put("authoritative", Boolean.valueOf(app.isAuthoritative()));
      }
      apps.add(row);
    }
    data.put("applications", apps);

    List<Map<String, Object>> workflows = new ArrayList<>();
    for (String name :
        new String[] {"MNB-Workflow-Joiner", "MNB-Workflow-Leaver", "MNB-Workflow-Access-Approval"}) {
      Workflow wf = ctx.getObjectByName(Workflow.class, name);
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("name", name);
      row.put("present", Boolean.valueOf(wf != null));
      workflows.add(row);
    }
    data.put("workflows", workflows);
    return MnbAgentSupport.ok("ENTERPRISE-STATUS", data);
  }

  @GET
  @Path("jml")
  @Produces(MediaType.APPLICATION_JSON)
  @RequiredRight("MNBToolkitAgent")
  public Map<String, Object> jml(@QueryParam("identity") String identityName) throws GeneralException {
    SailPointContext ctx = getContext();
    Map<String, Object> data = new LinkedHashMap<>();
    if (identityName == null || identityName.trim().isEmpty()) {
      data.put("hint", "Pass ?identity=helen.ross");
      return MnbAgentSupport.ok("ENTERPRISE-JML", data);
    }
    Identity id = ctx.getObjectByName(Identity.class, identityName.trim());
    if (id == null) {
      data.put("found", Boolean.FALSE);
      data.put("identity", identityName);
      return MnbAgentSupport.ok("ENTERPRISE-JML", data);
    }
    data.put("found", Boolean.TRUE);
    data.put("identity", id.getName());
    data.put("displayName", id.getDisplayName());
    data.put("inactive", Boolean.valueOf(id.isInactive()));
    data.put("manager", id.getManager() != null ? id.getManager().getName() : null);
    List<Link> links = id.getLinks();
    data.put("linkCount", Integer.valueOf(links != null ? links.size() : 0));
    List<Map<String, Object>> linkRows = new ArrayList<>();
    if (links != null) {
      for (Link link : links) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("application", link.getApplicationName());
        row.put("nativeIdentity", link.getNativeIdentity());
        row.put("disabled", Boolean.valueOf(link.isDisabled()));
        linkRows.add(row);
      }
    }
    data.put("links", linkRows);
    return MnbAgentSupport.ok("ENTERPRISE-JML", data);
  }
}
