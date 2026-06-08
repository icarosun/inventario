from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import (
    DepartmentForm,
    InventoryAuditForm,
    InventoryAuditReviewForm,
    InventoryAuditVerificationForm,
    InventoryImageForm,
    InventoryItemMovementForm,
    InventoryItemUpdateForm,
    InventoryItemForm,
)
from .models import (
    Department,
    InventoryAudit,
    InventoryAuditItem,
    InventoryItem,
    InventoryItemMovement,
)


class ItemListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    context_object_name = "items"
    paginate_by = 25
    template_name = "inventory/item_list.html"

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "created_by",
            "department",
            "updated_by",
        )
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(department__name__icontains=search)
                | Q(department__acronym__icontains=search)
            )
        return queryset


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = InventoryItem
    context_object_name = "item"
    template_name = "inventory/item_detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("department")


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Item criado com sucesso.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("inventory:item_detail", args=[self.object.pk])


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = InventoryItem
    form_class = InventoryItemUpdateForm
    template_name = "inventory/item_form.html"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Item atualizado com sucesso.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("inventory:item_detail", args=[self.object.pk])


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    context_object_name = "departments"
    paginate_by = 25
    template_name = "inventory/department_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(acronym__icontains=search)
            )
        return queryset


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = "inventory/department_form.html"
    success_url = reverse_lazy("inventory:department_list")

    def form_valid(self, form):
        messages.success(self.request, "Departamento criado com sucesso.")
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = "inventory/department_form.html"
    success_url = reverse_lazy("inventory:department_list")

    def form_valid(self, form):
        messages.success(self.request, "Departamento atualizado com sucesso.")
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Department
    template_name = "inventory/department_confirm_delete.html"
    success_url = reverse_lazy("inventory:department_list")

    def form_valid(self, form):
        messages.success(self.request, "Departamento removido com sucesso.")
        return super().form_valid(form)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class ItemDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = InventoryItem
    template_name = "inventory/item_confirm_delete.html"
    success_url = reverse_lazy("inventory:item_list")

    def form_valid(self, form):
        messages.success(self.request, "Item removido com sucesso.")
        return super().form_valid(form)


@login_required
def add_item_image(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        form = InventoryImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.item = item
            image.save()
            messages.success(request, "Imagem adicionada com sucesso.")
            return redirect("inventory:item_detail", pk=item.pk)
    else:
        form = InventoryImageForm()
    return render(request, "inventory/item_image_form.html", {"form": form, "item": item})


class AuditListView(LoginRequiredMixin, ListView):
    model = InventoryAudit
    context_object_name = "audits"
    template_name = "inventory/audit_list.html"


class AuditDetailView(LoginRequiredMixin, DetailView):
    model = InventoryAudit
    context_object_name = "audit"
    template_name = "inventory/audit_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = list(
            self.object.audit_items.select_related(
                "item", "found_department", "verified_by", "reviewed_by"
            )
        )
        context["records"] = records
        context["pending_count"] = sum(not record.is_verified for record in records)
        context["discrepancy_count"] = sum(record.has_discrepancy for record in records)
        context["review_pending_count"] = sum(
            record.has_discrepancy and not record.reviewed for record in records
        )
        context["verified_count"] = sum(record.is_verified for record in records)
        return context


class AuditCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = InventoryAudit
    form_class = InventoryAuditForm
    template_name = "inventory/audit_form.html"

    def form_valid(self, form):
        try:
            with transaction.atomic():
                form.instance.opened_by = self.request.user
                response = super().form_valid(form)
                items = InventoryItem.objects.filter(
                    status__in=[InventoryItem.Status.ACTIVE, InventoryItem.Status.NOT_FOUND]
                ).select_related("department")
                InventoryAuditItem.objects.bulk_create(
                    [
                        InventoryAuditItem(
                            audit=self.object,
                            item=item,
                            snapshot_name=item.name,
                            snapshot_department=str(item.department) if item.department else "",
                            snapshot_responsible_person=item.responsible_person,
                            snapshot_status=item.status,
                            snapshot_tombo_1=item.tombo_1,
                            snapshot_tombo_2=item.tombo_2,
                            snapshot_tombo_3=item.tombo_3,
                        )
                        for item in items
                    ]
                )
        except IntegrityError:
            form.add_error(None, "Ja existe uma auditoria aberta.")
            return self.form_invalid(form)
        messages.success(self.request, "Auditoria aberta com sucesso.")
        return response

    def get_success_url(self):
        return reverse("inventory:audit_detail", args=[self.object.pk])


class AuditVerificationView(LoginRequiredMixin, UpdateView):
    model = InventoryAuditItem
    form_class = InventoryAuditVerificationForm
    context_object_name = "record"
    template_name = "inventory/audit_verification_form.html"

    def dispatch(self, request, *args, **kwargs):
        record = self.get_object()
        if record.audit.status != InventoryAudit.Status.OPEN or record.reviewed:
            messages.error(request, "Esta conferencia nao pode mais ser alterada.")
            return redirect("inventory:audit_detail", pk=record.audit_id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.verified_by = self.request.user
        form.instance.verified_at = timezone.now()
        form.instance.reviewed = False
        form.instance.reviewed_by = None
        form.instance.reviewed_at = None
        messages.success(self.request, "Equipamento conferido com sucesso.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("inventory:audit_detail", args=[self.object.audit_id])


class AuditReviewView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = InventoryAuditItem
    form_class = InventoryAuditReviewForm
    context_object_name = "record"
    template_name = "inventory/audit_review_form.html"

    def dispatch(self, request, *args, **kwargs):
        record = self.get_object()
        if record.audit.status != InventoryAudit.Status.OPEN or not record.has_discrepancy:
            messages.error(request, "Esta conferencia nao possui divergencia pendente.")
            return redirect("inventory:audit_detail", pk=record.audit_id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        record = self.object
        item = record.item
        department = record.found_department if form.cleaned_data["apply_department"] else item.department
        responsible_person = (
            record.found_responsible_person
            if form.cleaned_data["apply_responsible_person"]
            else item.responsible_person
        )
        status = form.cleaned_data["applied_status"] or item.status
        applies_change = (
            form.cleaned_data["apply_department"]
            or form.cleaned_data["apply_responsible_person"]
            or form.cleaned_data["applied_status"]
        )
        marks_not_found_only = (
            record.located is False
            and form.cleaned_data["applied_status"] == InventoryItem.Status.NOT_FOUND
            and not form.cleaned_data["apply_department"]
            and not form.cleaned_data["apply_responsible_person"]
        )
        with transaction.atomic():
            if marks_not_found_only:
                item.status = InventoryItem.Status.NOT_FOUND
                item.updated_by = self.request.user
                item.save(update_fields=["status", "updated_by"])
            elif applies_change:
                record.movement = create_item_movement(
                    item=item,
                    user=self.request.user,
                    reason=f"Revisao da auditoria {record.audit.name}",
                    observation=record.observation,
                    photo=form.cleaned_data["movement_photo"],
                    return_caution_document=form.cleaned_data["return_caution_document"],
                    delivery_caution_document=form.cleaned_data["delivery_caution_document"],
                    department=department,
                    responsible_person=responsible_person,
                    status=status,
                )
            record.applied_department = form.cleaned_data["apply_department"]
            record.applied_responsible_person = form.cleaned_data["apply_responsible_person"]
            record.applied_status = form.cleaned_data["applied_status"]
            record.reviewed = True
            record.reviewed_by = self.request.user
            record.reviewed_at = timezone.now()
            record.save(
                update_fields=[
                    "movement",
                    "applied_department",
                    "applied_responsible_person",
                    "applied_status",
                    "reviewed",
                    "reviewed_by",
                    "reviewed_at",
                ]
            )
        messages.success(self.request, "Divergencia revisada com sucesso.")
        return redirect("inventory:audit_detail", pk=record.audit_id)


@login_required
def close_audit(request, pk):
    audit = get_object_or_404(InventoryAudit, pk=pk)
    if not request.user.is_staff:
        return HttpResponse(status=403)
    if request.method != "POST":
        return redirect("inventory:audit_detail", pk=audit.pk)
    records = list(audit.audit_items.all())
    if any(not record.is_verified for record in records):
        messages.error(request, "Existem equipamentos pendentes de conferencia.")
    elif any(record.has_discrepancy and not record.reviewed for record in records):
        messages.error(request, "Existem divergencias pendentes de revisao.")
    else:
        audit.status = InventoryAudit.Status.CLOSED
        audit.closed_by = request.user
        audit.closed_at = timezone.now()
        audit.save(update_fields=["status", "closed_by", "closed_at"])
        messages.success(request, "Auditoria encerrada com sucesso.")
    return redirect("inventory:audit_detail", pk=audit.pk)


@login_required
def export_audit_csv(request, pk):
    import csv

    audit = get_object_or_404(InventoryAudit, pk=pk)
    if not request.user.is_staff:
        return HttpResponse(status=403)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="auditoria-{audit.pk}.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Item", "Tombo 1", "Tombo 2", "Tombo 3/Serie", "Departamento registrado",
        "Responsavel registrado", "Localizado", "Condicao", "Departamento encontrado",
        "Responsavel encontrado", "Observacao", "Conferido por", "Conferido em",
        "Divergencia", "Revisado", "Revisado por", "Status aplicado",
    ])
    for record in audit.audit_items.select_related("found_department", "verified_by", "reviewed_by"):
        writer.writerow([
            record.snapshot_name,
            record.snapshot_tombo_1,
            record.snapshot_tombo_2,
            record.snapshot_tombo_3,
            record.snapshot_department,
            record.snapshot_responsible_person,
            "Sim" if record.located else "Nao" if record.located is False else "Pendente",
            record.get_condition_display() if record.condition else "",
            str(record.found_department) if record.found_department else "",
            record.found_responsible_person,
            record.observation,
            record.verified_by.username if record.verified_by else "",
            record.verified_at.isoformat() if record.verified_at else "",
            "Sim" if record.has_discrepancy else "Nao",
            "Sim" if record.reviewed else "Nao",
            record.reviewed_by.username if record.reviewed_by else "",
            record.get_applied_status_display() if record.applied_status else "",
        ])
    return response


def create_item_movement(*, item, user, reason, observation, photo, return_caution_document, delivery_caution_document, department, responsible_person, status):
    movement = InventoryItemMovement.objects.create(
        item=item,
        reason=reason,
        previous_department=str(item.department) if item.department else "",
        new_department=str(department) if department else "",
        previous_responsible_person=item.responsible_person,
        new_responsible_person=responsible_person,
        previous_status=item.status,
        new_status=status,
        observation=observation,
        photo=photo,
        return_caution_document=return_caution_document,
        delivery_caution_document=delivery_caution_document,
        moved_by=user,
    )
    item.department = department
    item.responsible_person = responsible_person
    item.status = status
    item.updated_by = user
    item.save(update_fields=["department", "responsible_person", "status", "updated_by"])
    return movement


@login_required
def move_item(request, pk):
    item = get_object_or_404(InventoryItem.objects.select_related("department"), pk=pk)
    if request.method == "POST":
        form = InventoryItemMovementForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                create_item_movement(
                    item=item,
                    user=request.user,
                    reason=form.cleaned_data["reason"],
                    observation=form.cleaned_data["observation"],
                    photo=form.cleaned_data["photo"],
                    return_caution_document=form.cleaned_data["return_caution_document"],
                    delivery_caution_document=form.cleaned_data["delivery_caution_document"],
                    department=form.cleaned_data["department"],
                    responsible_person=form.cleaned_data["responsible_person"],
                    status=form.cleaned_data["status"],
                )
            messages.success(request, "Movimentacao registrada com sucesso.")
            return redirect("inventory:item_detail", pk=item.pk)
    else:
        form = InventoryItemMovementForm(
            initial={
                "department": item.department,
                "responsible_person": item.responsible_person,
                "status": item.status,
            }
        )
    return render(request, "inventory/item_movement_form.html", {"form": form, "item": item})
