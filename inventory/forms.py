import json

from django import forms

from .models import Department, InventoryImage, InventoryItem


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name"]


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
