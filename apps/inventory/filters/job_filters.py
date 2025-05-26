from django_filters import rest_framework as filters
from ..models import Job
from datetime import datetime

class JobFilter(filters.FilterSet):
    reference = filters.CharFilter(field_name='reference', lookup_expr='icontains')
    date_estime = filters.CharFilter(method='filter_date_estime')
    equipe_nom = filters.CharFilter(field_name='jobdetail__pda__lebel', distinct=True)
    status = filters.CharFilter(field_name='status')

    class Meta:
        model = Job
        fields = ['reference', 'date_estime', 'equipe_nom', 'status']

    def filter_date_estime(self, queryset, name, value):
        try:
            # Essayer d'abord le format YYYY-MM-DD
            try:
                date_obj = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                # Si ça échoue, essayer le format DD-MM-YYYY
                date_obj = datetime.strptime(value, '%d-%m-%Y')
            
            # Convertir en format YYYY-MM-DD pour la requête
            formatted_date = date_obj.strftime('%Y-%m-%d')
            return queryset.filter(date_estime__date=formatted_date)
        except ValueError:
            return queryset.none() 