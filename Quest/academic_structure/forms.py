from django import forms
from .models import Institute, Department, Direction

class HierarchicalSelectionForm(forms.Form):
    institute = forms.ModelChoiceField(
        queryset=Institute.objects.all(),
        label="Выберите институт",
        empty_label="--- Все институты ---",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_institute'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        label="Выберите кафедру",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_department'})
    )
    direction = forms.ModelChoiceField(
        queryset=Direction.objects.none(),
        label="Выберите направление",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_direction'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'institute' in self.data:
            try:
                institute_id = int(self.data.get('institute'))
                self.fields['department'].queryset = Department.objects.filter(institute_id=institute_id).order_by(
                    'name')
            except (ValueError, TypeError):
                # Неверный institute_id или он отсутствует, queryset останется пустым (Department.objects.none())
                pass

        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['direction'].queryset = Direction.objects.filter(department_id=department_id).order_by(
                    'name')
            except (ValueError, TypeError):
                # Неверный department_id или он отсутствует, queryset останется пустым (Direction.objects.none())
                pass


class DirectionSearchForm(forms.Form):
    query = forms.CharField(
        label="Название направления",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите часть названия направления'})
    )