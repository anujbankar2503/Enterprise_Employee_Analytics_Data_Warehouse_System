from datetime import date


class _Field:
    """Descriptor base: validates a value every time it is set (encapsulation)."""
    nullable = False

    def __set_name__(self, owner, name):
        self.label = name
        self.attr = "_" + name

    def __get__(self, obj, objtype=None):
        return self if obj is None else getattr(obj, self.attr, None)

    def __set__(self, obj, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            if self.nullable:
                setattr(obj, self.attr, None)
                return
            raise ValueError(f"{self.label} is required")
        setattr(obj, self.attr, self.clean(value))

    def clean(self, value):
        return value


class _Text(_Field):
    def __init__(self, max_len, nullable=False):
        self.max_len, self.nullable = max_len, nullable

    def clean(self, value):
        value = str(value).strip()
        if len(value) > self.max_len:
            raise ValueError(f"{self.label} must be at most {self.max_len} characters")
        return value


class _Range(_Field):
    def __init__(self, low, high, nullable=False):
        self.low, self.high, self.nullable = low, high, nullable

    def clean(self, value):
        if not (self.low <= value <= self.high):
            raise ValueError(f"{self.label} must be between {self.low} and {self.high}")
        return value


class _Choice(_Field):
    def __init__(self, options, nullable=False):
        self.options, self.nullable = options, nullable

    def clean(self, value):
        if value not in self.options:
            raise ValueError(f"{self.label} must be one of {', '.join(self.options)}")
        return value


class _DateBetween(_Field):
    def __init__(self, low, high):
        self.low, self.high = low, high

    def clean(self, value):
        if not isinstance(value, date):
            raise ValueError(f"{self.label} must be a date")
        if not (self.low <= value <= self.high):
            raise ValueError(f"{self.label} must be between {self.low} and {self.high}")
        return value


class Employee:
    first_name = _Text(30)
    last_name = _Text(30)
    job_role = _Text(30)
    work_location = _Text(30)
    monthly_income = _Range(0, 10_000_000)
    job_level = _Range(1, 5)
    age = _Range(18, 100, nullable=True)
    education = _Range(1, 5, nullable=True)
    overtime = _Choice(("Yes", "No"))

    FIELDS = [
        "employee_id", "employee_number", "department_id", "first_name", "last_name",
        "hire_date", "job_role", "job_level", "gender", "work_location", "monthly_income",
        "age", "marital_status", "education", "education_field", "business_travel",
        "distance_from_home", "overtime", "total_working_years", "num_companies_worked",
    ]

    def __init__(self, first_name, last_name, department_id, hire_date, job_role,
                 monthly_income, job_level=1, gender=None, work_location="Pune",
                 age=None, marital_status=None, education=None, education_field=None,
                 business_travel=None, distance_from_home=None, overtime="No",
                 total_working_years=0, num_companies_worked=0,
                 employee_id=None, employee_number=None):
        self.employee_id = employee_id
        self.employee_number = employee_number
        self.department_id = department_id
        self.hire_date = hire_date
        self.gender = gender
        self.marital_status = marital_status
        self.education_field = education_field
        self.business_travel = business_travel
        self.distance_from_home = distance_from_home
        self.total_working_years = total_working_years
        self.num_companies_worked = num_companies_worked
        # validated attributes
        self.first_name = first_name
        self.last_name = last_name
        self.job_role = job_role
        self.work_location = work_location
        self.monthly_income = monthly_income
        self.job_level = job_level
        self.age = age
        self.education = education
        self.overtime = overtime

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {f: getattr(self, f) for f in self.FIELDS}


class Project:
    project_code = _Text(20)
    project_name = _Text(150)
    project_status = _Choice(("Planned", "Active", "Completed", "Cancelled"))

    def __init__(self, project_code, project_name, project_start_date,
                 planned_end_date=None, project_status="Planned", project_id=None):
        if planned_end_date and planned_end_date < project_start_date:
            raise ValueError("planned_end_date cannot be before project_start_date")
        self.project_id = project_id
        self.project_start_date = project_start_date
        self.planned_end_date = planned_end_date
        self.project_code = project_code
        self.project_name = project_name
        self.project_status = project_status

    def to_dict(self):
        return {
            "project_id": self.project_id, "project_code": self.project_code,
            "project_name": self.project_name, "project_status": self.project_status,
            "project_start_date": self.project_start_date,
            "planned_end_date": self.planned_end_date,
        }


class Review:
    performance_rating = _Range(1, 5)
    performance_score = _Range(0, 100)
    review_status = _Choice(("Pending", "Completed"))
    review_date = _DateBetween(date(2020, 1, 1), date(2030, 12, 31))

    def __init__(self, employee_id, review_date, performance_rating, performance_score,
                 project_id=None, reviewer_employee_id=None,
                 review_status="Completed", comments=None, review_id=None):
        if reviewer_employee_id is not None and reviewer_employee_id == employee_id:
            raise ValueError("An employee cannot review themselves")
        self.review_id = review_id
        self.employee_id = employee_id
        self.project_id = project_id
        self.reviewer_employee_id = reviewer_employee_id
        self.comments = comments
        self.review_date = review_date
        self.performance_rating = performance_rating
        self.performance_score = performance_score
        self.review_status = review_status

    def to_dict(self):
        return {
            "review_id": self.review_id, "employee_id": self.employee_id,
            "project_id": self.project_id, "review_date": self.review_date,
            "performance_rating": self.performance_rating,
            "performance_score": self.performance_score,
            "review_status": self.review_status,
        }