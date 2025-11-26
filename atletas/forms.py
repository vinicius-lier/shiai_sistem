from django import forms
from .models import Campeonato, FormaPagamento


class CampeonatoForm(forms.ModelForm):
    class Meta:
        model = Campeonato
        fields = "__all__"
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Campeonato Regional de Judô 2024',
                'required': True
            }),
            'data_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'data_competicao': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'data_limite_inscricao': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'regulamento': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 20,
                'placeholder': 'Digite o regulamento do campeonato...'
            }),
            'valor_inscricao_federado': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ex: 100.00'
            }),
            'valor_inscricao_nao_federado': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ex: 110.00'
            }),
            'chave_pix': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: 12345678900 ou email@exemplo.com'
            }),
            'titular_pix': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: João Silva'
            }),
            'formas_pagamento': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-checkbox-multiple'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }

