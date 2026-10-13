from django import forms

from .models import Session


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["title"]
        labels = {"title": "Talk title"}


class JoinForm(forms.Form):
    name = forms.CharField(max_length=100, required=False, label="Your name")
    anonymous = forms.BooleanField(required=False, label="Stay anonymous")

    def clean(self):
        data = super().clean()
        if not data.get("anonymous") and not (data.get("name") or "").strip():
            raise forms.ValidationError("Enter a name or tick anonymous.")
        return data
