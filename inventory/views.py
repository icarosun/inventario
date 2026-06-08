from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import DepartmentForm, InventoryImageForm, InventoryItemForm
from .models import Department, InventoryItem


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
                Q(name__icontains=search) | Q(department__name__icontains=search)
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
    form_class = InventoryItemForm
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
            queryset = queryset.filter(name__icontains=search)
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
