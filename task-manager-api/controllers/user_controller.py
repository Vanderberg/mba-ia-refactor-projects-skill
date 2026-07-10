from database import db
from models.user import User
from models.task import Task
from middlewares.errors import AppError, ValidationError, NotFoundError, ConflictError, UnauthorizedError, ForbiddenError
from utils.helpers import VALID_ROLES, MIN_PASSWORD_LENGTH, validate_email


class UserController:
    def list_users(self):
        result = []
        for u in User.query.all():
            user_data = {
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'active': u.active,
                'created_at': str(u.created_at),
                'task_count': len(u.tasks)
            }
            result.append(user_data)
        return result

    def get_user(self, user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        data = user.to_dict()
        tasks = Task.query.filter_by(user_id=user_id).all()
        data['tasks'] = [t.to_dict() for t in tasks]
        return data

    def create_user(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')

        if not validate_email(email):
            raise ValidationError('Email inválido')

        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha deve ter no mínimo 4 caracteres')

        existing = User.query.filter_by(email=email).first()
        if existing:
            raise ConflictError('Email já cadastrado')

        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"ERRO: {str(e)}")
            raise AppError('Erro ao criar usuário')

        print(f"Usuário criado: {user.id} - {user.name}")
        return user.to_dict()

    def update_user(self, user_id, data):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not validate_email(data['email']):
                raise ValidationError('Email inválido')

            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise AppError('Erro ao atualizar')

        return user.to_dict()

    def delete_user(self, user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = Task.query.filter_by(user_id=user_id).all()
        for t in tasks:
            db.session.delete(t)

        try:
            db.session.delete(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise AppError('Erro ao deletar')

        print(f"Usuário deletado: {user_id}")
        return {'message': 'Usuário deletado com sucesso'}

    def get_user_tasks(self, user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = Task.query.filter_by(user_id=user_id).all()
        result = []
        for t in tasks:
            task_data = {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(),
            }
            result.append(task_data)

        return result

    def login(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = User.query.filter_by(email=email).first()
        if not user:
            raise UnauthorizedError('Credenciais inválidas')

        if not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')

        if not user.active:
            raise ForbiddenError('Usuário inativo')

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': 'fake-jwt-token-' + str(user.id)
        }
