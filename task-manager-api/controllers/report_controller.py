from datetime import timedelta

from sqlalchemy import func

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from middlewares.errors import AppError, ValidationError, NotFoundError
from utils.helpers import calculate_percentage, utc_now


class ReportController:
    def summary_report(self):
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        p1 = Task.query.filter_by(priority=1).count()
        p2 = Task.query.filter_by(priority=2).count()
        p3 = Task.query.filter_by(priority=3).count()
        p4 = Task.query.filter_by(priority=4).count()
        p5 = Task.query.filter_by(priority=5).count()

        overdue_count = 0
        overdue_list = []
        for t in Task.query.all():
            if t.is_overdue():
                overdue_count += 1
                overdue_list.append({
                    'id': t.id,
                    'title': t.title,
                    'due_date': str(t.due_date),
                    'days_overdue': (utc_now() - t.due_date).days
                })

        seven_days_ago = utc_now() - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()

        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago
        ).count()

        total_by_user = dict(
            db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all()
        )
        done_by_user = dict(
            db.session.query(Task.user_id, func.count(Task.id))
            .filter(Task.status == 'done')
            .group_by(Task.user_id)
            .all()
        )

        user_stats = []
        for u in User.query.all():
            total = total_by_user.get(u.id, 0)
            completed = done_by_user.get(u.id, 0)
            user_stats.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total)
            })

        return {
            'generated_at': str(utc_now()),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'done': done,
                'cancelled': cancelled,
            },
            'tasks_by_priority': {
                'critical': p1,
                'high': p2,
                'medium': p3,
                'low': p4,
                'minimal': p5,
            },
            'overdue': {
                'count': overdue_count,
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = Task.query.filter_by(user_id=user_id).all()

        total = len(tasks)
        done = pending = in_progress = cancelled = overdue = high_priority = 0

        for t in tasks:
            if t.status == 'done':
                done += 1
            elif t.status == 'pending':
                pending += 1
            elif t.status == 'in_progress':
                in_progress += 1
            elif t.status == 'cancelled':
                cancelled += 1

            if t.priority <= 2:
                high_priority += 1

            if t.is_overdue():
                overdue += 1

        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(done, total)
            }
        }

    def list_categories(self):
        result = []
        for c in Category.query.all():
            cat_data = c.to_dict()
            cat_data['task_count'] = Task.query.filter_by(category_id=c.id).count()
            result.append(cat_data)
        return result

    def create_category(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', '#000000')

        try:
            db.session.add(category)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise AppError('Erro ao criar categoria')

        return category.to_dict()

    def update_category(self, cat_id, data):
        cat = Category.query.get(cat_id)
        if not cat:
            raise NotFoundError('Categoria não encontrada')

        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            cat.name = data['name']
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise AppError('Erro ao atualizar')

        return cat.to_dict()

    def delete_category(self, cat_id):
        cat = Category.query.get(cat_id)
        if not cat:
            raise NotFoundError('Categoria não encontrada')

        try:
            db.session.delete(cat)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise AppError('Erro ao deletar')

        return {'message': 'Categoria deletada'}
