from datetime import datetime

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from middlewares.errors import AppError, ValidationError, NotFoundError
from utils.helpers import (
    VALID_STATUSES,
    MIN_TITLE_LENGTH,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MAX_PRIORITY,
    calculate_percentage,
    utc_now,
)


class TaskController:
    def list_tasks(self):
        tasks = Task.query.all()

        user_ids = {t.user_id for t in tasks if t.user_id}
        category_ids = {t.category_id for t in tasks if t.category_id}

        users_by_id = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
        categories_by_id = (
            {c.id: c for c in Category.query.filter(Category.id.in_(category_ids)).all()} if category_ids else {}
        )

        result = []
        for t in tasks:
            task_data = t.to_dict()
            task_data['overdue'] = t.is_overdue()
            user = users_by_id.get(t.user_id) if t.user_id else None
            task_data['user_name'] = user.name if user else None
            category = categories_by_id.get(t.category_id) if t.category_id else None
            task_data['category_name'] = category.name if category else None
            result.append(task_data)

        return result

    def get_task(self, task_id):
        task = Task.query.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')

        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def create_task(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        if len(title) < MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')

        description = data.get('description', '')
        status = data.get('status', 'pending')
        priority = data.get('priority', 3)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        if status not in VALID_STATUSES:
            raise ValidationError('Status inválido')

        if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
            raise ValidationError('Prioridade deve ser entre 1 e 5')

        if user_id:
            user = User.query.get(user_id)
            if not user:
                raise NotFoundError('Usuário não encontrado')

        if category_id:
            cat = Category.query.get(category_id)
            if not cat:
                raise NotFoundError('Categoria não encontrada')

        task = Task()
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        if due_date:
            try:
                task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')

        if tags:
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        try:
            db.session.add(task)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar task: {str(e)}")
            raise AppError('Erro ao criar task')

        print(f"Task criada: {task.id} - {task.title}")
        return task.to_dict()

    def update_task(self, task_id, data):
        task = Task.query.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')

        if not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            if len(data['title']) < MIN_TITLE_LENGTH:
                raise ValidationError('Título muito curto')
            if len(data['title']) > MAX_TITLE_LENGTH:
                raise ValidationError('Título muito longo')
            task.title = data['title']

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if data['status'] not in VALID_STATUSES:
                raise ValidationError('Status inválido')
            task.status = data['status']

        if 'priority' in data:
            if data['priority'] < MIN_PRIORITY or data['priority'] > MAX_PRIORITY:
                raise ValidationError('Prioridade deve ser entre 1 e 5')
            task.priority = data['priority']

        if 'user_id' in data:
            if data['user_id']:
                user = User.query.get(data['user_id'])
                if not user:
                    raise NotFoundError('Usuário não encontrado')
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id']:
                cat = Category.query.get(data['category_id'])
                if not cat:
                    raise NotFoundError('Categoria não encontrada')
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
                except ValueError:
                    raise ValidationError('Formato de data inválido')
            else:
                task.due_date = None

        if 'tags' in data:
            task.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']

        task.updated_at = utc_now()

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise AppError('Erro ao atualizar')

        print(f"Task atualizada: {task.id}")
        return task.to_dict()

    def delete_task(self, task_id):
        task = Task.query.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')

        try:
            db.session.delete(task)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise AppError('Erro ao deletar')

        print(f"Task deletada: {task_id}")
        return {'message': 'Task deletada com sucesso'}

    def search_tasks(self, args):
        query = args.get('q', '')
        status = args.get('status', '')
        priority = args.get('priority', '')
        user_id = args.get('user_id', '')

        tasks = Task.query

        if query:
            tasks = tasks.filter(
                db.or_(
                    Task.title.like(f'%{query}%'),
                    Task.description.like(f'%{query}%')
                )
            )

        if status:
            tasks = tasks.filter(Task.status == status)

        if priority:
            tasks = tasks.filter(Task.priority == int(priority))

        if user_id:
            tasks = tasks.filter(Task.user_id == int(user_id))

        return [t.to_dict() for t in tasks.all()]

    def get_stats(self):
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue_count,
            'completion_rate': calculate_percentage(done, total),
        }
