# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

from buildbot.interfaces import ITriggerableScheduler
from buildbot.process.buildstep import LoggingBuildStep, BuildStep, SUCCESS, FAILURE, EXCEPTION
from buildbot.process.properties import Properties, Property
from twisted.python import log
from twisted.internet import defer
from buildbot import config
from buildbot.status.results import DEPENDENCY_FAILURE


class Trigger(LoggingBuildStep):
    name = "Trigger"

    renderables = [ 'set_properties', 'schedulerNames', 'sourceStamps',
                    'updateSourceStamp', 'alwaysUseLatest' ]

    flunkOnFailure = True

    def __init__(self, schedulerNames=[], sourceStamp = None, sourceStamps = None,
                 updateSourceStamp=None, alwaysUseLatest=False,
                 waitForFinish=False, set_properties={}, 
                 copy_properties=[], **kwargs):
        if not schedulerNames:
            config.error(
                "You must specify a scheduler to trigger")
        if (sourceStamp or sourceStamps) and (updateSourceStamp is not None):
            config.error(
                "You can't specify both sourceStamps and updateSourceStamp")
        if (sourceStamp or sourceStamps) and alwaysUseLatest:
            config.error(
                "You can't specify both sourceStamps and alwaysUseLatest")
        if alwaysUseLatest and (updateSourceStamp is not None):
            config.error(
                "You can't specify both alwaysUseLatest and updateSourceStamp"
            )
        self.schedulerNames = schedulerNames
        self.sourceStamps = sourceStamps or []
        if sourceStamp:
            self.sourceStamps.append(sourceStamp)
        if updateSourceStamp is not None:
            self.updateSourceStamp = updateSourceStamp
        else:
            self.updateSourceStamp = not (alwaysUseLatest or self.sourceStamps)
        self.alwaysUseLatest = alwaysUseLatest
        self.waitForFinish = waitForFinish
        properties = {}
        properties.update(set_properties)
        for i in copy_properties:
            properties[i] = Property(i)
        self.set_properties = properties
        self.running = False
        self.ended = False
        LoggingBuildStep.__init__(self, **kwargs)

    def interrupt(self, reason):
        if self.running:
            BuildStep.interrupt(self, reason)
            if self.step_status.isWaitingForLocks():
                self.addCompleteLog('interrupt while waiting for locks', str(reason))
            else:
                self.addCompleteLog('interrupt', str(reason))

            self.running = False
            self.finished(EXCEPTION)

    # Create the properties that are used for the trigger
    def createTriggerProperties(self):
        # make a new properties object from a dict rendered by the old
        # properties object
        trigger_properties = Properties()
        trigger_properties.update(self.set_properties, "Trigger")
        return trigger_properties

    # Get all scheduler instances that were configured
    # A tuple of (triggerables, invalidnames) is returned
    def getSchedulers(self):
        all_schedulers = self.build.builder.botmaster.parent.allSchedulers()
        all_schedulers = dict([(sch.name, sch) for sch in all_schedulers])
        invalid_schedulers = []
        triggered_schedulers = []
        # don't fire any schedulers if we discover an unknown one
        for scheduler in self.schedulerNames:
            scheduler = scheduler
            if all_schedulers.has_key(scheduler):
                sch = all_schedulers[scheduler]
                if ITriggerableScheduler.providedBy(sch):
                    triggered_schedulers.append(sch)
                else:
                    invalid_schedulers.append(scheduler)
            else:
                invalid_schedulers.append(scheduler)

        return (triggered_schedulers, invalid_schedulers)

    def prepareSourcestampListForTrigger(self):
        if self.sourceStamps:
            ss_for_trigger = {}
            for ss in self.sourceStamps:
                codebase = ss.get('codebase','')
                assert codebase not in ss_for_trigger, "codebase specified multiple times"
                ss_for_trigger[codebase] = ss
            return ss_for_trigger

        if self.alwaysUseLatest:
            return {}

        # start with the sourcestamps from current build
        ss_for_trigger = {}
        objs_from_build = self.build.getAllSourceStamps()
        for ss in objs_from_build:
            ss_for_trigger[ss.codebase] = ss.asDict()

        # overrule revision in sourcestamps with got revision
        if self.updateSourceStamp:
            got = self.build.build_status.getAllGotRevisions()
            for codebase in ss_for_trigger:
                if codebase in got:
                    ss_for_trigger[codebase]['revision'] = got[codebase]

        return ss_for_trigger

    def finishIfRunning(self, result):
        if self.running:
            self.finished(result)

    @defer.inlineCallbacks
    def start(self):
        # Get all triggerable schedulers and check if there are invalid schedules
        (triggered_schedulers, invalid_schedulers) = self.getSchedulers()
        if invalid_schedulers:
            self.step_status.setText(['not valid scheduler:'] + invalid_schedulers)
            self.finished(FAILURE)
            return

        self.running = True

        props_to_set = self.createTriggerProperties()

        ss_for_trigger = self.prepareSourcestampListForTrigger()

        dl = []
        triggered_names = []
        triggeredbybrid = None
        try:
            triggeredbybrid = self.build.requests[0].id
        except TypeError as e:
            log.msg("Warning: check self.build.requests type expecting a list, trigger.py \n%s" % e.message)

        for sch in triggered_schedulers:
            dl.append(sch.trigger(ss_for_trigger, set_props=props_to_set, triggeredbybrid=triggeredbybrid, reason=self.build.build_status.getReason()))
            triggered_names.append("'%s'" % sch.name)
        self.step_status.setText(['Triggered:'] + triggered_names)

        if self.waitForFinish:
            rclist = yield defer.DeferredList(dl, consumeErrors=True)
        else:
            # do something to handle errors
            for d in dl:
                d.addErrback(log.err,
                    '(ignored) while invoking Triggerable schedulers:')
            rclist = None
            self.finishIfRunning(SUCCESS)
            return

        was_exception = was_failure = False
        brids = {}
        for was_cb, results in rclist:
            if isinstance(results, tuple):
                results, some_brids = results
                brids.update(some_brids)

            if not was_cb:
                was_exception = True
                log.err(results)
                continue

            if results == FAILURE:
                was_failure = True

        if was_exception or was_failure:
            result = DEPENDENCY_FAILURE
            self.step_status.setText(["Dependency failed to build."])
            self.step_status.setText2(["(dependency failed to build)"])
        else:
            result = SUCCESS

        if brids:
            master = self.build.builder.botmaster.parent

            def getBuildResults(build):
                if 'results' in build:
                    return (build['results'],)
                return ()

            @defer.inlineCallbacks
            def add_links_multimaster(res):
                # reverse the dictionary lookup for brid to builder name
                brid_to_bn = dict((_brid,_bn) for _bn,_brid in brids.iteritems())
                for was_cb, builddicts in res:
                    if was_cb:
                        for build in builddicts:
                            bn = brid_to_bn[build['brid']]
                            builder = master.getStatus().getBuilder(bn)
                            if builder is not None:
                                friendly_name = builder.friendly_name
                            else:
                                friendly_name = None
                            num = build['number']
                            url = yield master.status.getURLForBuildRequest(build['brid'], bn, num,
                                                                            friendly_name, self.sourceStamps)
                            self.step_status.addURL(url['text'], url['path'], *getBuildResults(build))
            
            def add_links(res):
                # reverse the dictionary lookup for brid to builder name
                brid_to_bn = dict((_brid,_bn) for _bn,_brid in brids.iteritems())
                for was_cb, builddicts in res:
                    if was_cb:
                        for build in builddicts:
                            bn = brid_to_bn[build['brid']]
                            builder = master.getStatus().getBuilder(bn)
                            if builder is not None:
                                friendly_name = builder.friendly_name
                            else:
                                friendly_name = None
                            num = build['number']
                            url = master.status.getURLForBuild(bn, num, friendly_name, self.sourceStamps)
                            self.step_status.addURL(url['text'], url['path'], *getBuildResults(build))

            builddicts = [master.db.builds.getBuildsAndResultForRequest(br) for br in brids.values()]
            res_builds = yield defer.DeferredList(builddicts, consumeErrors=True)
            if master.config.multiMaster:
                yield add_links_multimaster(res_builds)
            else:
                add_links(res_builds)

        self.finishIfRunning(result)
        return
