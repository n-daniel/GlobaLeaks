from globaleaks.transactors.base import MacroOperation

from globaleaks.models.node import Node
from globaleaks.models.context import Context
from globaleaks.models.receiver import Receiver
from globaleaks.models.externaltip import File, ReceiverTip, WhistleblowerTip, Comment
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.submission import Submission
from globaleaks.plugins.manager import PluginManager

from globaleaks.rest.errors import ForbiddenOperation, InvalidInputFormat
from globaleaks.settings import transact


class CrudOperations(MacroOperation):
    """
    README.md describe pattern and reasons
    """

    # Below CrudOperations for Admin API

    @transact
    def get_node(self):
        node_iface = Node(self.store)
        node_description_dict = node_iface.get_single()

        self.returnData(node_description_dict)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_node(self, request):
        node_iface = Node(self.store)
        node_description_dict = node_iface.update(request)

        self.returnData(node_description_dict)
        self.returnCode(201)
        return self.prepareRetVals()

    @transact
    def get_context_list(self):
        context_iface = Context(self.store)
        all_contexts = context_iface.get_all()

        self.returnData(all_contexts)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def create_context(self, request):

        context_iface = Context(self.store)

        context_description_dict = context_iface.new(request)
        new_context_gus = context_description_dict['context_gus']

        # 'receivers' it's a relationship between two tables, and is managed
        # with a separate method of new()
        receiver_iface = Receiver(self.store)

        context_iface.context_align(new_context_gus, request['receivers'])
        receiver_iface.full_receiver_align(new_context_gus, request['receivers'])

        context_description = context_iface.get_single(new_context_gus)

        self.returnData(context_description)
        self.returnCode(201)
        return self.prepareRetVals()


    @transact
    def get_context(self, context_gus):

        context_iface = Context(self.store)
        context_description = context_iface.get_single(context_gus)

        self.returnData(context_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_context(self, context_gus, request):


        context_iface = Context(self.store)
        context_iface.update(context_gus, request)

        # 'receivers' it's a relationship between two tables, and is managed
        # with a separate method of update()
        receiver_iface = Receiver(self.store)
        context_iface.context_align(context_gus, request['receivers'])
        receiver_iface.full_receiver_align(context_gus, request['receivers'])

        context_description = context_iface.get_single(context_gus)

        self.returnData(context_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def delete_context(self, context_gus):
        """
        This DELETE operation, its permanent, and remove all the reference
        a Context has within the system (Tip, File, submission...)
        """
        # Get context description, just to verify that context_gus is valid
        context_iface = Context(self.store)
        context_desc = context_iface.get_single(context_gus)

        # Collect tip by context and iter on the list
        receivertip_iface = ReceiverTip(self.store)
        tips_related_blocks = receivertip_iface.get_tips_by_context(context_gus)

        internaltip_iface = InternalTip(self.store)
        whistlebtip_iface = WhistleblowerTip(self.store)
        file_iface = File(self.store)
        comment_iface = Comment(self.store)

        # For every InternalTip, delete comment, wTip, rTip and Files
        for tip_block in tips_related_blocks:

            internaltip_id = tip_block.get('internaltip')['internaltip_id']

            whistlebtip_iface.delete_access_by_itip(internaltip_id)
            receivertip_iface.massive_delete(internaltip_id)
            comment_iface.delete_comment_by_itip(internaltip_id)
            file_iface.delete_file_by_itip(internaltip_id)

            # and finally, delete the InternalTip
            internaltip_iface.tip_delete(internaltip_id)

        # (Just a consistency check - need to be removed)
        receiver_iface = Receiver(self.store)
        receivers_associated = receiver_iface.get_receivers_by_context(context_gus)
        print "receiver associated by context POV:", len(receivers_associated),\
        "receiver associated by context DB-field:", len(context_desc['receivers'])

        # Align all the receiver associated to the context, that the context cease to exist
        receiver_iface.align_context_delete(context_desc['receivers'], context_gus)

        # Get the submission list under the context, and delete all of them
        submission_iface = Submission(self.store)
        submission_list = submission_iface.get_all()
        for single_sub in submission_list:
            submission_iface.submission_delete(single_sub['submission_gus'], wb_request=False)

        # Finally, delete the context
        context_iface.delete_context(context_gus)

        self.returnData(context_desc)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_receiver_list(self):

        receiver_iface = Receiver(self.store)
        all_receivers = receiver_iface.get_all()

        self.returnData(all_receivers)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def create_receiver(self, request):
        receiver_iface = Receiver(self.store)

        new_receiver = receiver_iface.new(request)
        new_receiver_gus = new_receiver['receiver_gus']

        # 'contexts' it's a relationship between two tables, and is managed
        # with a separate method of new()
        context_iface = Context(self.store)
        receiver_iface.receiver_align(new_receiver_gus, request['contexts'])
        context_iface.full_context_align(new_receiver_gus, request['contexts'])

        new_receiver_desc = receiver_iface.get_single(new_receiver_gus)

        self.returnData(new_receiver_desc)
        self.returnCode(201)
        return self.prepareRetVals()

    @transact
    def get_receiver(self, receiver_gus):
        receiver_iface = Receiver(self.store)
        receiver_description = receiver_iface.get_single(receiver_gus)

        self.returnData(receiver_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_receiver(self, receiver_gus, request):
        receiver_iface = Receiver(self.store)
        receiver_iface.update(receiver_gus, request)

        # 'contexts' it's a relationship between two tables, and is managed
        # with a separate method of update()

        context_iface = Context(self.store)
        receiver_iface.receiver_align(receiver_gus, request['contexts'])
        context_iface.full_context_align(receiver_gus, request['contexts'])

        receiver_description = receiver_iface.get_single(receiver_gus)

        self.returnData(receiver_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def delete_receiver(self, receiver_gus):
        receiver_iface = Receiver(self.store)
        receiver_desc = receiver_iface.get_single(receiver_gus)

        receivertip_iface = ReceiverTip(self.store)
        # Remove Tip possessed by the receiver
        related_tips = receivertip_iface.get_tips_by_receiver(receiver_gus)
        for tip in related_tips:
            receivertip_iface.personal_delete(tip['tip_gus'])
            # Remind: the comment are kept, and the name do not use a reference
            # but is stored in the comment entry.

        context_iface = Context(self.store)

        # Just an alignment check that need to be removed
        contexts_associated = context_iface.get_contexts_by_receiver(receiver_gus)
        print "context associated by receiver POV:", len(contexts_associated),\
        "context associated by receiver-DB field:", len(receiver_desc['contexts'])

        context_iface.align_receiver_delete(receiver_desc['contexts'], receiver_gus)

        # Finally delete the receiver
        receiver_iface.receiver_delete(receiver_gus)

        self.returnData(receiver_desc)
        self.returnCode(200)
        return self.prepareRetVals()

    # Completed CrudOperations for the Admin API
    # Below CrudOperations for Receiver API

    @transact
    def get_receiver_by_receiver(self, receiver_gus):
        receiver_desc = Receiver(self.store).get_single(receiver_gus)

        self.returnData(receiver_desc)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_receiver_by_receiver(self, receiver_gus, request):
        updated_receiver_desc = Receiver(self.store).self_update(receiver_gus, request)

        # context_iface = Context(store)
        # context_iface.update_languages(updated_receiver_desc['contexts'])
        # TODO implement this function

        self.returnData(updated_receiver_desc)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_tip_list(self, valid_tip):
        receivertip_iface = ReceiverTip(self.store)

        tips = receivertip_iface.get_tips_by_tip(valid_tip)
        # this function return a dict with: { 'othertips': [$rtip], 'request' : $rtip }

        tips['othertips'].append(tips['request'])

        self.returnData(tips)
        self.returnCode(200)
        return self.prepareRetVals()

    # Completed CrudOperations for the Receiver API
    # Below CrudOperations for Tip API

    @transact
    def get_tip_by_receiver(self, tip_gus):

        requested_t = ReceiverTip(self.store)
        tip_description = requested_t.get_single(tip_gus)

        # Get also the file list, along with the download path
        file_list = File(store).get_files_by_itip(tip_description['internaltip_id'])
        tip_description.update({'folders' : [
                            { "name": "hardcoded_block",
                              "uploaded_date" : "Wed Feb  6 10:35:42 2013",
                              "files": [ file_list ]
                            }
                    ]})

        self.returnData(tip_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_tip_by_wb(self, receipt):
        requested_t = WhistleblowerTip(self.store)
        tip_description = requested_t.get_single(receipt)

        # Get also the file list, along with the download path
        file_list = File(store).get_files_by_itip(tip_description['internaltip_id'])
        tip_description.update({'folders' : file_list})

        self.returnData(tip_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_tip_by_receiver(self, tip_gus, request):
        receivertip_iface = ReceiverTip(self.store)

        if request['personal_delete']:
            receivertip_iface.personal_delete(tip_gus)

        elif request['is_pertinent']:
            # elif is used to avoid the message with both delete+pertinence.
            # This operation is based in ReceiverTip and is returned
            # the sum of the vote expressed. This value is updated in InternalTip
            (itip_id, vote_sum) = receivertip_iface.pertinence_vote(tip_gus, request['is_pertinent'])

            internaltip_iface = InternalTip(self.store)
            internaltip_iface.update_pertinence(itip_id, vote_sum)

        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def delete_tip(self, tip_gus):
        receivertip_iface = ReceiverTip(self.store)

        receivers_map = receivertip_iface.get_receivers_by_tip(tip_gus)

        if not receivers_map['actor']['can_delete_submission']:
            raise ForbiddenOperation

        # sibilings_tips has the keys: 'sibilings': [$] 'requested': $
        sibilings_tips = receivertip_iface.get_sibiligs_by_tip(tip_gus)

        # delete all the related tip
        for sibiltip in sibilings_tips['sibilings']:
            receivertip_iface.personal_delete(sibiltip['tip_gus'])

        # and the tip of the called
        receivertip_iface.personal_delete(sibilings_tips['requested']['tip_gus'])

        # extract the internaltip_id, we need for the next operations
        itip_id = sibilings_tips['requested']['internaltip_id']

        # remove all the files: XXX think if delivery method need to be inquired
        file_iface = File(self.store)
        files_list = file_iface.get_files_by_itip(itip_id)

        # remove all the comments based on a specific itip_id
        comment_iface = Comment(self.store)
        comments_list = comment_iface.delete_comment_by_itip(itip_id)

        internaltip_iface = InternalTip(self.store)
        # finally, delete the internaltip
        internaltip_iface.tip_delete(sibilings_tips['requested']['internaltip_id'])

        # XXX Notify Tip removal to the receivers ?
        # XXX ask to the deleter a comment about the action, notifiy this comment ?

        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_comment_list_by_receiver(self, tip_gus):
        requested_t = ReceiverTip(self.store)
        tip_description = requested_t.get_single(tip_gus)

        comment_iface = Comment(self.store)
        comment_list = comment_iface.get_comment_by_itip(tip_description['internaltip_id'])

        self.returnData(comment_list)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_comment_list_by_wb(self, receipt):
        requested_t = WhistleblowerTip(self.store)
        tip_description = requested_t.get_single(receipt)

        comment_iface = Comment(self.store)
        comment_list = comment_iface.get_comment_by_itip(tip_description['internaltip_id'])

        self.returnData(comment_list)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def new_comment_by_receiver(self, tip_gus, request):
        requested_t = ReceiverTip(self.store)
        tip_description = requested_t.get_single(tip_gus)

        comment_iface = Comment(self.store)

        comment_stored = comment_iface.new(tip_description['internaltip_id'],
            request['content'], u"receiver", tip_description['receiver_gus'])
        # XXX here can be put the name of the Receiver

        self.returnData(comment_stored)
        self.returnCode(201)
        return self.prepareRetVals()

    @transact
    def new_comment_by_wb(self, receipt, request):
        requested_t = WhistleblowerTip(self.store)
        tip_description = requested_t.get_single(receipt)

        comment_iface = Comment(self.store)

        comment_stored = comment_iface.new(tip_description['internaltip_id'],
            request['content'], u"whistleblower")

        self.returnData(comment_stored)
        self.returnCode(201)
        return self.prepareRetVals()


    @transact
    def get_receiver_list_by_receiver(self, tip_gus):
        requested_t = ReceiverTip(self.store)
        tip_description = requested_t.get_single(tip_gus)

        itip_iface = InternalTip(self.store)
        inforet = itip_iface.get_receivers_by_itip(tip_description['internaltip_id'])

        self.returnData(inforet)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_receiver_list_by_wb(self, receipt):
        requested_t = WhistleblowerTip(self.store)
        tip_description = requested_t.get_single(receipt)

        receiver_iface = Receiver(self.store)

        itip_iface = InternalTip(self.store)
        # inforet = itip_iface.get_receivers_by_itip(tip_description['internaltip_id'])
        # the wb, instead get the list of active receiver, is getting the list of receiver
        # configured in the context:
        receivers_selected = itip_iface.get_single(tip_description['internaltip_id'])['receivers']

        inforet = []
        for receiver_gus in receivers_selected:
            inforet.append(receiver_iface.get_single(receiver_gus))

        self.returnData(inforet)
        self.returnCode(200)
        return self.prepareRetVals()

    # Completed CrudOperations for the Tip API
    # Below CrudOperations for Submission API

    @transact
    def new_submission(self, request):
        context_desc = Context(self.store).get_single(request['context_gus'])

        if not context_desc['selectable_receiver']:
            request.update({'receivers' : context_desc['receivers'] })

        submission_desc = Submission(self.store).new(request)

        if submission_desc['finalize']:

            internaltip_desc =  InternalTip(self.store).new(submission_desc)

            wbtip_desc = WhistleblowerTip(self.store).new(internaltip_desc)

            File(self.store).switch_reference(submission_desc, internaltip_desc)

            submission_desc.update({'receipt' : wbtip_desc['receipt']})
        else:
            submission_desc.update({'receipt' : ''})

        self.returnData(submission_desc)
        self.returnCode(201) # Created
        return self.prepareRetVals()

    @transact
    def get_submission(self, submission_gus):
        submission_desc = Submission(self.store).get_single(submission_gus)

        self.returnData(submission_desc)
        self.returnCode(201) # Created
        return self.prepareRetVals()

    @transact
    def update_submission(self, submission_gus, request):
        context_desc = Context(self.store).get_single(request['context_gus'])

        if not context_desc['selectable_receiver']:
            request.update({'receivers' : context_desc['receivers'] })

        submission_desc = Submission(self.store).update(submission_gus, request)

        if submission_desc['finalize']:

            internaltip_desc =  InternalTip(self.store).new(submission_desc)

            wbtip_desc = WhistleblowerTip(self.store).new(internaltip_desc)

            File(self.store).switch_reference(submission_desc, internaltip_desc)

            submission_desc.update({'receipt' : wbtip_desc['receipt']})
        else:
            submission_desc.update({'receipt' : ''})

        self.returnData(submission_desc)
        self.returnCode(202) # Updated
        return self.prepareRetVals()

    @transact
    def delete_submission(self, submission_gus):
        Submission(self.store).submission_delete(submission_gus, wb_request=True)

        self.returnCode(200)
        return self.prepareRetVals()

    # Completed CrudOperations for the Submission API
    # Below CrudOperations for Debug API

    @transact
    def dump_models(self, expected):

        expected_dict = { 'itip' : InternalTip,
                          'wtip' : WhistleblowerTip,
                          'rtip' : ReceiverTip,
                          'receivers' : Receiver,
                          'comment' : Comment,
                          'file' : File,
                          'submission' : Submission,
                          'contexts' : Context }

        outputDict = {}
        self.returnCode(200)

        if expected in ['count', 'all']:

            for key, object in expected_dict.iteritems():
                info_list = object(self.store).get_all()

                if expected == 'all':
                    outputDict.update({key : info_list})

                outputDict.update({("%s_elements" % key) : len(info_list) })

            self.returnData(outputDict)
            return self.prepareRetVals()

        # XXX plugins is not dumped with all or count!
        if expected == 'plugins':

            info_list = PluginManager.get_all()
            outputDict.update({expected : info_list, ("%s_elements" % expected) : len(info_list) })

            self.returnData(outputDict)
            return self.prepareRetVals()

        if expected_dict.has_key(expected):

            info_list = expected_dict[expected](self.store).get_all()
            outputDict.update({expected : info_list, ("%s_elements" % expected) : len(info_list) })

            self.returnData(outputDict)
            return self.prepareRetVals()

        raise InvalidInputFormat("Not acceptable '%s'" % expected)




