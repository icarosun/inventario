import json

from django import forms

from .models import (
    Department,
    InventoryItemMovement,
    InventoryAudit,
    InventoryAuditItem,
    InventoryImage,
    InventoryItem,
)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "acronym"]


class InventoryItemForm(forms.ModelForm):
    specs = forms.CharField(
        label="Especificacoes JSON",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text='Exemplo: {"marca": "Dell", "memoria": "16GB"}',
    )

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "description",
            "department",
            "responsible_person",
            "immediate_supervisor",
            "status",
            "tombo_1",
            "tombo_2",
            "tombo_3",
            "specs",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and isinstance(self.instance.specs, dict):
            self.initial["specs"] = json.dumps(
                self.instance.specs,
                ensure_ascii=True,
                indent=2,
            )

    def clean_specs(self):
        value = self.cleaned_data["specs"]
        if not value:
            return {}
        try:
            data = json.loads(value)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError("Informe um JSON valido.") from exc
        if not isinstance(data, dict):
            raise forms.ValidationError("As especificacoes devem ser um objeto JSON.")
        return data


class InventoryImageForm(forms.ModelForm):
    class Meta:
        model = InventoryImage
        fields = ["image", "caption"]


class InventoryAuditForm(forms.ModelForm):
    class Meta:
        model = InventoryAudit
        fields = ["name", "deadline"]
        widgets = {"deadline": forms.DateInput(attrs={"type": "date"})}


class InventoryAuditVerificationForm(forms.ModelForm):
    class Meta:
        model = InventoryAuditItem
        fields = [
            "located",
            "condition",
            "found_department",
            "found_responsible_person",
            "observation",
            "evidence_image",
        ]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("located") is None:
            self.add_error("located", "Informe se o equipamento foi localizado.")
        if not cleaned_data.get("condition"):
            self.add_error("condition", "Informe a condicao do equipamento.")
        return cleaned_data


class InventoryAuditReviewForm(forms.ModelForm):
    class Meta:
        model = InventoryAuditItem
        fields = []
    apply_department = forms.BooleanField(label="Aplicar departamento encontrado", required=False)
    apply_responsible_person = forms.BooleanField(label="Aplicar responsavel encontrado", required=False)
    applied_status = forms.ChoiceField(
        label="Novo status oficial",
        choices=[("", "Manter status atual"), *InventoryItem.Status.choices],
        required=False,
    )
    movement_photo = forms.ImageField(label="Foto da movimentacao", required=False)
    return_caution_document = forms.FileField(label="Cautela de devolucao", required=False)
    delivery_caution_document = forms.FileField(label="Cautela de entrega", required=False)

    def clean(self):
        cleaned_data = super().clean()
        applies_change = (
            cleaned_data.get("apply_department")
            or cleaned_data.get("apply_responsible_person")
            or cleaned_data.get("applied_status")
        )
        marks_not_found_only = (
            self.instance.located is False
            and cleaned_data.get("applied_status") == InventoryItem.Status.NOT_FOUND
            and not cleaned_data.get("apply_department")
            and not cleaned_data.get("apply_responsible_person")
        )
        if applies_change and not marks_not_found_only and not cleaned_data.get("movement_photo"):
            self.add_error("movement_photo", "A foto e obrigatoria ao atualizar o inventario.")
        if applies_change and not marks_not_found_only and not cleaned_data.get("delivery_caution_document"):
            self.add_error("delivery_caution_document", "A cautela de entrega e obrigatoria ao atualizar o inventario.")
        return cleaned_data


class InventoryItemUpdateForm(InventoryItemForm):
    class Meta(InventoryItemForm.Meta):
        fields = [
            "name",
            "category",
            "description",
            "immediate_supervisor",
            "tombo_1",
            "tombo_2",
            "tombo_3",
            "specs",
        ]


class InventoryItemMovementForm(forms.Form):
    department = forms.ModelChoiceField(label="Novo departamento", queryset=Department.objects.all(), required=False)
    responsible_person = forms.CharField(label="Novo responsavel", max_length=150, required=False)
    status = forms.ChoiceField(label="Novo status", choices=InventoryItem.Status.choices)
    reason = forms.CharField(label="Motivo", max_length=200)
    observation = forms.CharField(label="Observacao", widget=forms.Textarea, required=False)
    photo = forms.ImageField(label="Foto da movimentacao")
    return_caution_document = forms.FileField(label="Cautela de devolucao", required=False)
    delivery_caution_document = forms.FileField(label="Cautela de entrega")
