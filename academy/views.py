from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from dr_toister_site.telegram_notifications import (
    notify_course_application_created,
)

from .forms import CourseApplicationForm
from .models import (
    Course,
    CourseEnrollment,
)


def course_list(request):
    selected_audience = request.GET.get(
        "audience",
        "",
    )

    valid_audiences = {
        Course.Audience.EVERYONE,
        Course.Audience.COSMETOLOGISTS,
    }

    if (
            selected_audience
            not in valid_audiences
    ):
        selected_audience = ""

    courses = Course.objects.filter(
        is_published=True,
    ).order_by(
        "start_date",
        "title",
    )

    public_courses = courses.filter(
        audience=Course.Audience.EVERYONE,
    )

    professional_courses = courses.filter(
        audience=(
            Course.Audience.COSMETOLOGISTS
        ),
    )

    if (
            selected_audience
            == Course.Audience.EVERYONE
    ):
        page_title = "Школа догляду"
        page_description = (
            "Зрозумілі програми для тих, хто хоче "
            "краще розуміти свою шкіру, косметичні "
            "засоби та домашній догляд."
        )
    elif (
            selected_audience
            == Course.Audience.COSMETOLOGISTS
    ):
        page_title = (
            "Підвищення кваліфікації"
        )
        page_description = (
            "Професійні програми для практикуючих "
            "косметологів і спеціалістів "
            "індустрії краси."
        )
    else:
        page_title = "Навчання"
        page_description = (
            "Школа догляду для клієнтів і "
            "професійне підвищення кваліфікації "
            "для косметологів."
        )

    context = {
        "public_courses": public_courses,
        "professional_courses": (
            professional_courses
        ),
        "selected_audience": (
            selected_audience
        ),
        "page_title": page_title,
        "page_description": (
            page_description
        ),
    }

    return render(
        request,
        "academy/course_list.html",
        context,
    )


def course_detail(request, pk):
    course = get_object_or_404(
        Course,
        pk=pk,
        is_published=True,
    )

    form = CourseApplicationForm(
        request.POST or None,
        user=request.user,
    )

    if (
            request.method == "POST"
            and form.is_valid()
    ):
        applicant_phone = (
            form.cleaned_data[
                "applicant_phone"
            ]
        )

        with transaction.atomic():
            locked_course = (
                Course.objects
                .select_for_update()
                .get(
                    pk=course.pk,
                    is_published=True,
                )
            )

            duplicate_filters = Q(
                applicant_phone=(
                    applicant_phone
                )
            )

            if request.user.is_authenticated:
                duplicate_filters |= Q(
                    student=request.user
                )

            existing_application = (
                CourseEnrollment.objects
                .filter(
                    duplicate_filters,
                    course=locked_course,
                )
                .exclude(
                    status=(
                        CourseEnrollment
                        .Status.CANCELLED
                    )
                )
                .order_by(
                    "-enrolled_at"
                )
                .first()
            )

            if existing_application:
                request.session[
                    "last_course_application_id"
                ] = existing_application.pk

                messages.info(
                    request,
                    (
                        "Заявка на цю програму "
                        "з таким номером телефону "
                        "вже існує."
                    ),
                )

                return redirect(
                    "academy:application-success",
                    application_id=(
                        existing_application.pk
                    ),
                )

            application = (
                CourseEnrollment.objects.create(
                    student=(
                        request.user
                        if (
                            request.user
                            .is_authenticated
                        )
                        else None
                    ),
                    applicant_name=(
                        form.cleaned_data[
                            "applicant_name"
                        ]
                    ),
                    applicant_phone=(
                        applicant_phone
                    ),
                    applicant_comment=(
                        form.cleaned_data[
                            "applicant_comment"
                        ]
                    ),
                    course=locked_course,
                    created_by=(
                        request.user
                        if (
                            request.user
                            .is_authenticated
                        )
                        else None
                    ),
                    source=(
                        CourseEnrollment
                        .Source.ONLINE
                    ),
                )
            )

            request.session[
                "last_course_application_id"
            ] = application.pk

            transaction.on_commit(
                lambda application_id=(
                    application.pk
                ): (
                    notify_course_application_created(
                        application_id
                    )
                )
            )

        return redirect(
            "academy:application-success",
            application_id=application.pk,
        )

    return render(
        request,
        "academy/course_detail.html",
        {
            "course": course,
            "form": form,
        },
    )


def application_success(
        request,
        application_id,
):
    last_application_id = (
        request.session.get(
            "last_course_application_id"
        )
    )

    if (
            last_application_id
            != application_id
    ):
        raise Http404(
            "Заявку не знайдено."
        )

    application = get_object_or_404(
        CourseEnrollment.objects
        .select_related("course"),
        pk=application_id,
    )

    return render(
        request,
        "academy/application_success.html",
        {
            "application": application,
        },
    )
