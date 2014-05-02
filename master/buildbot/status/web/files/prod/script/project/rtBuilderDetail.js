define(["jquery","realtimePages","helpers","dataTables","handlebars","extend-moment","libs/jquery.form","text!templates/builderdetail.handlebars","timeElements","rtGenericTable"],function(e,t,n,r,i,s,o,u,a,f){var l,c,h,p,d=Handlebars.compile(u);return l={init:function(){c=l.currentBuildsTableInit(e("#rtCurrentBuildsTable")),h=l.pendingBuildsTableInit(e("#rtPendingBuildsTable")),p=f.table.buildTableInit(e("#rtBuildsTable"));var r=t.defaultRealtimeFunctions();r.project=l.rtfProcessCurrentBuilds,r.pending_builds=l.rtfProcessPendingBuilds,r.builds=l.rtfProcessBuilds,t.initRealtime(r),window.location.search!==""&&n.codeBaseBranchOverview(e("#brancOverViewCont"))},rtfProcessCurrentBuilds:function(e){a.clearTimeObjects(c),c.fnClearTable();try{e.currentBuilds!==undefined&&(c.fnAddData(e.currentBuilds),a.updateTimeObjects()),a.updateTimeObjects()}catch(t){}},rtfProcessPendingBuilds:function(e){a.clearTimeObjects(h),h.fnClearTable(),n.selectBuildsAction(h);try{h.fnAddData(e),a.updateTimeObjects()}catch(t){}},rtfProcessBuilds:function(e){f.table.rtfProcessBuilds(p,e)},currentBuildsTableInit:function(t){var i={};return i.aoColumns=[{mData:null,sTitle:"#"},{mData:null,sTitle:"Current build",sWidth:"200px"},{mData:null,sTitle:"Revision"},{mData:null,sTitle:"Author"}],i.aoColumnDefs=[f.cell.buildID(0),{aTargets:[1],sClass:"txt-align-left",mRender:function(t,n,r){var i={showRunningBuilds:!0},s=e.extend(i,r);return d(s)},fnCreatedCell:function(t){n.delegateToProgressBar(e(t).find(".percent-outer-js"))}},f.cell.revision(2),{aTargets:[3],sClass:"txt-align-left",mRender:function(t,n,r){var i="N/A";return e.each(r.properties,function(e,t){t[0]==="owner"&&(i=t[1])}),i}}],r.initTable(t,i)},pendingBuildsTableInit:function(t){var n={};return n.aoColumns=[{mData:null},{mData:null},{mData:null,sWidth:"80px"}],n.aoColumnDefs=[{aTargets:[0],sClass:"txt-align-left",mRender:function(e,t,n){return s.getDateFormatted(n.submittedAt)}},{aTargets:[1],sClass:"txt-align-left",mRender:function(){return d({pendingBuildWait:!0})},fnCreatedCell:function(t,n,r){a.addElapsedElem(e(t).find(".waiting-time-js"),r.submittedAt)}},{aTargets:[2],sClass:"txt-align-right",mRender:function(e,t,n){return d({removeBuildSelector:!0,data:n})}}],r.initTable(t,n)}},l});