define(["jquery","dataTables","timeElements","text!hbCells","extend-moment","handlebars"],function(e,t,n,r,i){var s=Handlebars.compile(r),o={getPropertyOnData:function(e,t){return t instanceof String?e[t]:t(e)}},u={revision:function(e){return{aTargets:[e],sClass:"txt-align-left",mRender:function(e,t,n){return s({revisionCell:!0,data:n})}}},buildID:function(e){return{aTargets:[e],sClass:"txt-align-left",mRender:function(e,t,n){return s({buildID:!0,data:n})}}},buildStatus:function(t){return{aTargets:[t],sClass:"txt-align-left",mRender:function(e,t,n){return s({buildStatus:!0,build:n})},fnCreatedCell:function(t,n,r){e(t).removeClass().addClass(r.results_text)}}},shortTime:function(e,t){return{aTargets:[e],sClass:"txt-align-left",mRender:function(e,n,r){var s=o.getPropertyOnData(r,t);return i.getDateFormatted(s)}}}},a={buildTableInit:function(e){var n={};return n.aoColumns=[{mData:null,sTitle:"#"},{mData:null,sTitle:"Date",sWidth:"50px"},{mData:null,sTitle:"Revision"},{mData:null,sTitle:"Result"},{mData:null,sTitle:"Slave",sWidth:"110px"}],n.aoColumnDefs=[u.buildID(0),u.shortTime(1,function(e){return e.times[0]}),u.revision(2),u.buildStatus(3),{aTargets:[4],sClass:"txt-align-left",mRender:function(e,t,n){return n.slave_friendly_name}}],t.initTable(e,n)},rtfProcessBuilds:function(e,t){n.clearTimeObjects(e),e.fnClearTable();try{e.fnAddData(t),n.updateTimeObjects()}catch(r){}}};return{table:a,cell:u}});