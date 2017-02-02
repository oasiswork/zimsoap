from . import ZObject


# class Contact(AbstractAddressableZObject):
class Contact(ZObject):
    """A contact object
    """
    TAG_NAME = 'contact'
    SELECTORS = 'email'


class FilterRule(ZObject):
    """ A mailbox filter rule object
    """
    TAG_NAME = 'filter'
    ATTRNAME_PROPERTY = 'name'


class Task(ZObject):
    TAG_NAME = 'task'
    ATTRNAME_PROPERTY = 'id'

    def to_creator(self, subject, desc):
        """ Return a python-zimbra dict for CreateTaskRequest

        Example :
        <CreateTaskRequest>
            <m su="Task subject">
                <inv>
                    <comp name="Task subject">
                        <fr>Task comment</fr>
                        <desc>Task comment</desc>
                    </comp>
                </inv>
                <mp>
                    <content/>
                </mp>
            </m>
        </CreateTaskRequest>
        """

        task = {
            'm': {
                'su': subject,
                'inv': {
                    'comp': {
                        'name': subject,
                        'fr': {'_content': desc},
                        'desc': {'_content': desc},
                        'percentComplete': '0'
                    }
                },
                'mp': {
                    'content': {}
                }
            }
        }

        return task
