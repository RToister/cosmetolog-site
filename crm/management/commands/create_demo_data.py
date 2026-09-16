from datetime import time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db import transaction
from django.utils import timezone

from academy.models import Course, CourseEnrollment
from appointments.models import Booking, VisitComment
from crm.models import Customer
from schedule.models import BlockedDate, WorkingHour
from services.models import (
    Procedure,
    ProcedureCategory,
)
from shop.models import (
    Order,
    OrderItem,
    Product,
    ProductCategory,
)

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Очищає локальні бізнес-дані та створює "
        "демонстраційну базу DR TOISTER."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help=(
                "Підтверджує очищення наявних "
                "бізнес-даних."
            ),
        )

    def ensure_local_environment(self, clear):
        if not settings.DEBUG:
            raise CommandError(
                "Команду дозволено запускати лише "
                "при DEBUG=True."
            )

        database = settings.DATABASES["default"]

        if (
                database["ENGINE"]
                != "django.db.backends.sqlite3"
        ):
            raise CommandError(
                "Команда призначена лише для "
                "локальної SQLite-бази."
            )

        if not clear:
            raise CommandError(
                "Для очищення даних додайте "
                "прапорець --clear."
            )

    def clear_business_data(self):
        self.stdout.write(
            "Очищення бізнес-даних..."
        )

        VisitComment.objects.all().delete()
        Booking.objects.all().delete()

        OrderItem.objects.all().delete()
        Order.objects.all().delete()

        CourseEnrollment.objects.all().delete()
        Customer.objects.all().delete()

        Product.objects.all().delete()
        ProductCategory.objects.all().delete()

        Course.objects.all().delete()

        Procedure.objects.all().delete()
        ProcedureCategory.objects.all().delete()

        BlockedDate.objects.all().delete()
        WorkingHour.objects.all().delete()

        User.objects.filter(
            is_staff=False,
        ).delete()

    def create_working_hours(self):
        for day_of_week in range(7):
            WorkingHour.objects.create(
                day_of_week=day_of_week,
                start_time=time(8, 0),
                end_time=time(21, 0),
                is_active=True,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Створено графік: щодня 08:00–21:00."
            )
        )

    def create_procedures(self):
        injection_category = (
            ProcedureCategory.objects.create(
                name="Ін’єкційна косметологія",
                description=(
                    "Ін’єкційні процедури для "
                    "корекції та омолодження."
                ),
            )
        )

        skincare_category = (
            ProcedureCategory.objects.create(
                name="Догляд за шкірою",
                description=(
                    "Професійні процедури очищення "
                    "та відновлення шкіри."
                ),
            )
        )

        consultation_category = (
            ProcedureCategory.objects.create(
                name="Консультації",
                description=(
                    "Консультації "
                    "косметолога-дерматолога."
                ),
            )
        )

        return {
            "consultation": Procedure.objects.create(
                category=consultation_category,
                name="Консультація косметолога",
                description=(
                    "Оцінка стану шкіри та складання "
                    "індивідуального плану догляду."
                ),
                duration_minutes=60,
                price=Decimal("800.00"),
                is_active=True,
            ),
            "botox": Procedure.objects.create(
                category=injection_category,
                name="Ботулінотерапія",
                description=(
                    "Корекція мімічних зморшок."
                ),
                duration_minutes=60,
                price=Decimal("3500.00"),
                is_active=True,
            ),
            "mesotherapy": Procedure.objects.create(
                category=injection_category,
                name="Мезотерапія обличчя",
                description=(
                    "Ін’єкційне зволоження та "
                    "відновлення шкіри."
                ),
                duration_minutes=90,
                price=Decimal("2800.00"),
                is_active=True,
            ),
            "cleaning": Procedure.objects.create(
                category=skincare_category,
                name="Комбінована чистка обличчя",
                description=(
                    "Комплексне очищення шкіри."
                ),
                duration_minutes=90,
                price=Decimal("1600.00"),
                is_active=True,
            ),
            "peeling": Procedure.objects.create(
                category=skincare_category,
                name="Хімічний пілінг",
                description=(
                    "Оновлення текстури та тону шкіри."
                ),
                duration_minutes=60,
                price=Decimal("1400.00"),
                is_active=True,
            ),
        }

    def create_products(self):
        skincare = ProductCategory.objects.create(
            name="Домашній догляд",
            description=(
                "Косметика для щоденного "
                "домашнього догляду."
            ),
        )

        professional = ProductCategory.objects.create(
            name="Препарати для спеціалістів",
            description=(
                "Професійні препарати та засоби "
                "для використання косметологами."
            ),
        )

        return {
            "cleanser": Product.objects.create(
                category=skincare,
                name="Очищувальний гель",
                sku="DRT-CLEAN-001",
                description=(
                    "М’який гель для щоденного "
                    "очищення."
                ),
                usage_recommendations=(
                    "Використовувати вранці "
                    "та ввечері."
                ),
                retail_price=Decimal("780.00"),
                professional_price=Decimal("590.00"),
                availability=(
                    Product.Availability.PUBLIC
                ),
                stock_quantity=25,
                is_active=True,
            ),
            "cream": Product.objects.create(
                category=skincare,
                name="Відновлювальний крем",
                sku="DRT-CREAM-001",
                description=(
                    "Крем для відновлення захисного "
                    "бар’єра шкіри."
                ),
                usage_recommendations=(
                    "Наносити після очищення."
                ),
                retail_price=Decimal("1150.00"),
                professional_price=Decimal("870.00"),
                availability=(
                    Product.Availability.PUBLIC
                ),
                stock_quantity=18,
                is_active=True,
            ),
            "spf": Product.objects.create(
                category=skincare,
                name="Сонцезахисний крем SPF 50",
                sku="DRT-SPF-001",
                description=(
                    "Щоденний захист шкіри "
                    "від ультрафіолету."
                ),
                usage_recommendations=(
                    "Наносити за 15 хвилин "
                    "до виходу."
                ),
                retail_price=Decimal("980.00"),
                professional_price=Decimal("740.00"),
                availability=(
                    Product.Availability.PUBLIC
                ),
                stock_quantity=30,
                is_active=True,
            ),
            "serum": Product.objects.create(
                category=skincare,
                name="Зволожувальна сироватка",
                sku="DRT-SERUM-001",
                description=(
                    "Сироватка з гіалуроновою "
                    "кислотою."
                ),
                usage_recommendations=(
                    "Наносити перед кремом."
                ),
                retail_price=Decimal("1350.00"),
                professional_price=Decimal("990.00"),
                availability=(
                    Product.Availability.PUBLIC
                ),
                stock_quantity=20,
                is_active=True,
            ),
            "professional_mask": (
                Product.objects.create(
                    category=professional,
                    name=(
                        "Професійна альгінатна маска"
                    ),
                    sku="DRT-PRO-MASK-001",
                    description=(
                        "Професійна маска для "
                        "кабінетного використання."
                    ),
                    usage_recommendations=(
                        "Використовувати відповідно "
                        "до професійного протоколу."
                    ),
                    retail_price=None,
                    professional_price=(
                        Decimal("650.00")
                    ),
                    availability=(
                        Product.Availability
                        .PROFESSIONALS_ONLY
                    ),
                    stock_quantity=15,
                    is_active=True,
                )
            ),
        }

    def create_users_and_customers(
            self,
            admin_user,
    ):
        demo_users = {
            "maria": {
                "username": "demo_maria",
                "first_name": "Марія",
                "last_name": "Коваль",
                "email": "maria@example.com",
                "phone_number": "+380501112233",
                "user_type": User.UserType.CLIENT,
            },
            "olena": {
                "username": "demo_olena",
                "first_name": "Олена",
                "last_name": "Бондар",
                "email": "olena@example.com",
                "phone_number": "+380502223344",
                "user_type": (
                    User.UserType.COSMETOLOGIST
                ),
            },
        }

        users = {}

        for key, user_data in demo_users.items():
            user = User.objects.create(
                **user_data,
            )
            user.set_unusable_password()
            user.save(
                update_fields=("password",)
            )
            users[key] = user

        users["olena"].verify_cosmetologist(
            verified_by=admin_user,
        )

        customers = {}

        customer_data = [
            (
                "maria",
                "Марія Коваль",
                "+380501112233",
                Customer.CustomerType.CLIENT,
                "Чутлива шкіра. Перший візит.",
                users["maria"],
            ),
            (
                "olena",
                "Олена Бондар",
                "+380502223344",
                Customer.CustomerType.COSMETOLOGIST,
                "Практикуючий косметолог.",
                users["olena"],
            ),
            (
                "anna",
                "Анна Мельник",
                "+380503334455",
                Customer.CustomerType.CLIENT,
                "Цікавиться домашнім доглядом.",
                None,
            ),
            (
                "sofia",
                "Софія Шевченко",
                "+380504445566",
                Customer.CustomerType.CLIENT,
                "",
                None,
            ),
            (
                "natalia",
                "Наталія Ткаченко",
                "+380505556677",
                Customer.CustomerType.COSMETOLOGIST,
                (
                    "Цікавиться професійним "
                    "навчанням."
                ),
                None,
            ),
        ]

        for (
                key,
                full_name,
                phone_number,
                customer_type,
                notes,
                user,
        ) in customer_data:
            customer, created = (
                Customer.objects.get_or_create_by_phone(
                    full_name=full_name,
                    phone_number=phone_number,
                    user=user,
                    customer_type=customer_type,
                )
            )

            customer.notes = notes
            customer.is_active = True
            customer.save(
                update_fields=(
                    "notes",
                    "is_active",
                    "updated_at",
                )
            )

            customers[key] = customer

        return users, customers

    def create_bookings(
            self,
            procedures,
            customers,
            admin_user,
    ):
        today = timezone.localdate()

        booking_data = [
            (
                customers["maria"],
                procedures["consultation"],
                today + timedelta(days=1),
                time(9, 0),
                Booking.Status.CONFIRMED,
                (
                    "Потрібна консультація "
                    "щодо догляду."
                ),
            ),
            (
                customers["anna"],
                procedures["cleaning"],
                today + timedelta(days=1),
                time(11, 0),
                Booking.Status.PENDING,
                "Перший візит.",
            ),
            (
                customers["sofia"],
                procedures["peeling"],
                today + timedelta(days=2),
                time(10, 0),
                Booking.Status.CONFIRMED,
                "",
            ),
            (
                customers["maria"],
                procedures["botox"],
                today + timedelta(days=3),
                time(13, 0),
                Booking.Status.PENDING,
                (
                    "Уточнити зони перед "
                    "процедурою."
                ),
            ),
            (
                customers["natalia"],
                procedures["mesotherapy"],
                today + timedelta(days=4),
                time(15, 0),
                Booking.Status.CONFIRMED,
                "",
            ),
        ]

        bookings = []

        for (
                customer,
                procedure,
                booking_date,
                start_time,
                status,
                client_note,
        ) in booking_data:
            booking = Booking.objects.create(
                client=customer.user,
                customer=customer,
                procedure=procedure,
                client_name=customer.full_name,
                client_phone=customer.phone_number,
                date=booking_date,
                start_time=start_time,
                status=status,
                source=Booking.Source.ADMIN,
                client_note=client_note,
                created_by=admin_user,
            )

            bookings.append(booking)

        VisitComment.objects.create(
            booking=bookings[0],
            author=admin_user,
            comment=(
                "Проведено первинну оцінку "
                "стану шкіри."
            ),
            recommendations=(
                "Використовувати м’яке очищення, "
                "зволожувальний крем та SPF 50."
            ),
        )

        return bookings

    def create_orders(
            self,
            products,
            users,
            customers,
            admin_user,
    ):
        first_order = Order.objects.create(
            client=users["maria"],
            customer=customers["maria"],
            client_name=(
                customers["maria"].full_name
            ),
            client_phone=(
                customers["maria"].phone_number
            ),
            created_by=admin_user,
            status=Order.Status.PENDING,
            source=Order.Source.ONLINE,
            payment_method=(
                Order.PaymentMethod.CARD
            ),
        )

        OrderItem.objects.create(
            order=first_order,
            product=products["cleanser"],
            quantity=1,
        )

        OrderItem.objects.create(
            order=first_order,
            product=products["spf"],
            quantity=1,
        )

        first_order.mark_as_paid()

        second_order = Order.objects.create(
            customer=customers["anna"],
            client_name=(
                customers["anna"].full_name
            ),
            client_phone=(
                customers["anna"].phone_number
            ),
            created_by=admin_user,
            status=Order.Status.PENDING,
            source=Order.Source.CLINIC,
            payment_method=(
                Order.PaymentMethod.CASH
            ),
        )

        OrderItem.objects.create(
            order=second_order,
            product=products["cream"],
            quantity=1,
        )

        second_order.mark_as_paid()

        third_order = Order.objects.create(
            client=users["olena"],
            customer=customers["olena"],
            client_name=(
                customers["olena"].full_name
            ),
            client_phone=(
                customers["olena"].phone_number
            ),
            created_by=admin_user,
            status=Order.Status.PENDING,
            source=Order.Source.CLINIC,
            payment_method=(
                Order.PaymentMethod.BANK_TRANSFER
            ),
        )

        OrderItem.objects.create(
            order=third_order,
            product=products["serum"],
            quantity=2,
        )

        OrderItem.objects.create(
            order=third_order,
            product=products[
                "professional_mask"
            ],
            quantity=2,
        )

        third_order.mark_as_paid()

        pending_order = Order.objects.create(
            customer=customers["sofia"],
            client_name=(
                customers["sofia"].full_name
            ),
            client_phone=(
                customers["sofia"].phone_number
            ),
            created_by=admin_user,
            status=Order.Status.PENDING,
            source=Order.Source.ONLINE,
            payment_method="",
        )

        OrderItem.objects.create(
            order=pending_order,
            product=products["spf"],
            quantity=1,
        )

    def create_courses(
            self,
            users,
            customers,
            admin_user,
    ):
        today = timezone.localdate()

        skincare_course = Course.objects.create(
            title="Базовий домашній догляд",
            description=(
                "Практичний курс із підбору "
                "щоденного догляду за шкірою."
            ),
            audience=Course.Audience.EVERYONE,
            training_type=(
                Course.TrainingType.GROUP
            ),
            format=Course.Format.ONLINE,
            duration_hours=4,
            price=Decimal("1200.00"),
            start_date=(
                    today + timedelta(days=14)
            ),
            location="Онлайн",
            is_published=True,
        )

        professional_course = (
            Course.objects.create(
                title="Професійні пілінги",
                description=(
                    "Поглиблений курс для "
                    "практикуючих косметологів."
                ),
                audience=(
                    Course.Audience.COSMETOLOGISTS
                ),
                training_type=(
                    Course.TrainingType.BOTH
                ),
                format=Course.Format.HYBRID,
                duration_hours=12,
                price=Decimal("6500.00"),
                start_date=(
                        today + timedelta(days=30)
                ),
                location="Клініка DR TOISTER",
                is_published=True,
            )
        )

        CourseEnrollment.objects.create(
            student=users["maria"],
            customer=customers["maria"],
            applicant_name=(
                customers["maria"].full_name
            ),
            applicant_phone=(
                customers["maria"].phone_number
            ),
            applicant_comment=(
                "Хочу покращити домашній догляд."
            ),
            course=skincare_course,
            created_by=admin_user,
            status=(
                CourseEnrollment.Status.CONFIRMED
            ),
            source=(
                CourseEnrollment.Source.ONLINE
            ),
        )

        CourseEnrollment.objects.create(
            student=users["olena"],
            customer=customers["olena"],
            applicant_name=(
                customers["olena"].full_name
            ),
            applicant_phone=(
                customers["olena"].phone_number
            ),
            applicant_comment=(
                "Цікавить індивідуальний формат."
            ),
            course=professional_course,
            created_by=admin_user,
            status=(
                CourseEnrollment.Status.COMPLETED
            ),
            source=(
                CourseEnrollment.Source.CLINIC
            ),
        )

        CourseEnrollment.objects.create(
            customer=customers["natalia"],
            applicant_name=(
                customers["natalia"].full_name
            ),
            applicant_phone=(
                customers["natalia"].phone_number
            ),
            applicant_comment=(
                "Потрібні деталі програми."
            ),
            course=professional_course,
            created_by=admin_user,
            status=(
                CourseEnrollment.Status.PENDING
            ),
            source=(
                CourseEnrollment.Source.ONLINE
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.ensure_local_environment(
            options["clear"]
        )

        admin_user = User.objects.filter(
            is_superuser=True,
            is_active=True,
        ).order_by("pk").first()

        if admin_user is None:
            raise CommandError(
                "Активного superuser не знайдено. "
                "Спочатку створіть адміністратора."
            )

        self.stdout.write(
            self.style.WARNING(
                "Буде очищено локальні "
                "бізнес-дані. Обліковий запис "
                "адміністратора буде збережено."
            )
        )

        self.clear_business_data()
        self.create_working_hours()

        procedures = self.create_procedures()
        products = self.create_products()

        users, customers = (
            self.create_users_and_customers(
                admin_user
            )
        )

        bookings = self.create_bookings(
            procedures,
            customers,
            admin_user,
        )

        self.create_orders(
            products,
            users,
            customers,
            admin_user,
        )

        self.create_courses(
            users,
            customers,
            admin_user,
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Демонстраційну базу створено."
            )
        )

        self.stdout.write(
            f"Клієнтів CRM: "
            f"{Customer.objects.count()}"
        )

        self.stdout.write(
            f"Процедур: "
            f"{Procedure.objects.count()}"
        )

        self.stdout.write(
            f"Товарів: "
            f"{Product.objects.count()}"
        )

        self.stdout.write(
            f"Записів: {len(bookings)}"
        )

        self.stdout.write(
            f"Замовлень: "
            f"{Order.objects.count()}"
        )

        self.stdout.write(
            f"Курсів: {Course.objects.count()}"
        )

        self.stdout.write(
            "Графік: щодня з 08:00 до 21:00."
        )
