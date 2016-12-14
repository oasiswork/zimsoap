from zimsoap import zobjects


class MethodMixin:
    def create_task(self, subject, desc):
        """Create a task

        :param subject: the task's subject
        :param desc: the task's content in plain-text
        :returns: the task's id
        """
        task = zobjects.Task()
        task_creator = task.to_creator(subject, desc)
        resp = self.request('CreateTask', task_creator)
        task_id = resp['calItemId']
        return task_id

    def get_task(self, task_id):
        """Retrieve one task, discriminated by id.

        :param: task_id: the task id

        :returns: a zobjects.Task object ;
                  if no task is matching, returns None.
        """
        task = self.request_single('GetTask', {'id': task_id})

        if task:
            return zobjects.Task.from_dict(task)
        else:
            return None
