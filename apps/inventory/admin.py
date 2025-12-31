from django.contrib import admin
from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.db import transaction, connection
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
import re

from .models import Personne


# ---------------- Resources ---------------- #

class PersonneResource(resources.ModelResource):
    """
    Resource pour l'import/export des personnes.
    Importe/exporte les champs en accord avec le modèle Personne.
    """
    numero = fields.Field(column_name='numero', attribute='numero')
    full_name = fields.Field(column_name='full_name', attribute='full_name')
    reference = fields.Field(column_name='reference', attribute='reference', readonly=True)

    class Meta:
        model = Personne
        fields = ('reference', 'numero', 'full_name')
        import_id_fields = ('numero',)

    def before_save_instance(self, instance, row, **kwargs):
        """
        Génère automatiquement la référence si elle est vide avant la sauvegarde,
        utilisant la méthode du modèle Personne pour garantir l'unicité et la présence du préfixe.
        Args:
            instance: L'instance Personne à sauvegarder
            row: Les données de la ligne importée (dict)
        """
        if not instance.reference:
            instance.save()
            if not instance.reference:
                instance.reference = instance.generate_reference('PER')


# ---------------- Forms ---------------- #

class CreatePersonnesForm(forms.Form):
    """Formulaire pour créer des personnes"""
    
    nombre_personnes = forms.IntegerField(
        label='Nombre de personnes',
        required=True,
        min_value=1,
        max_value=9999,
        help_text='Nombre de personnes à créer (format: opr-0001, opr-0002, ...)'
    )
    
    def clean_nombre_personnes(self):
        nombre = self.cleaned_data.get('nombre_personnes')
        if nombre and nombre > 9999:
            raise forms.ValidationError('Le nombre maximum de personnes est 9999.')
        return nombre


# ---------------- Admin ---------------- #

@admin.register(Personne)
class PersonneAdmin(ImportExportModelAdmin):
    """
    Admin pour le modèle Personne sans affichage du champ 'reference' en interface.
    """
    resource_class = PersonneResource
    list_display = ('numero', 'full_name')
    search_fields = ('numero', 'full_name')
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted', 'reference')
    readonly_fields = ()
    
    # Spécifier explicitement le template pour le changelist
    change_list_template = 'admin/inventory/personne/change_list.html'

    def get_form(self, request, obj=None, **kwargs):
        """
        Permet de cacher complètement le champ 'reference' du formulaire d'admin,
        que ce soit à la création ou à l'édition.
        """
        form = super().get_form(request, obj, **kwargs)
        if 'reference' in form.base_fields:
            form.base_fields['reference'].widget = forms.HiddenInput()
            form.base_fields['reference'].required = False
        return form
    
    def get_urls(self):
        """Ajouter les URLs personnalisées pour la création de personnes"""
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path(
                'create-personnes/',
                self.admin_site.admin_view(self.create_personnes_view),
                name='inventory_personne_create_personnes',
            ),
        ]
        return custom_urls + urls
    
    def create_personnes_view(self, request):
        """Vue pour créer des personnes en masse avec logique optimisée"""
        
        if request.method == 'POST':
            form = CreatePersonnesForm(request.POST)
            if form.is_valid():
                nombre_personnes = form.cleaned_data['nombre_personnes']
                
                # Plage de numéros disponibles : 0001 à 99999999 (pour supporter les grands numéros avec 3 zéros)
                range_start = 1
                range_end = 99999999

                # Trouver le prochain numéro disponible de manière optimisée
                next_available_num = None

                # Utiliser la méthode Django qui fonctionne avec tous les formats existants
                existing_numeros = Personne.objects.filter(
                    numero__startswith='opr-'
                ).values_list('numero', flat=True)

                # Extraire rapidement les numéros existants dans la plage
                existing_nums_set = set()
                for numero in existing_numeros:
                    match = re.match(r'opr-(\d+)', numero)
                    if match:
                        num = int(match.group(1))
                        if range_start <= num <= range_end:
                            existing_nums_set.add(num)

                # Trouver le prochain numéro disponible
                for num in range(range_start, range_end + 1):
                    if num not in existing_nums_set:
                        next_available_num = num
                        break
                    # Récupérer uniquement les numéros dans la plage avec une requête optimisée
                    existing_numeros = Personne.objects.filter(
                        numero__startswith='opr-'
                    ).values_list('numero', flat=True)
                    
                    # Extraire rapidement les numéros existants dans la plage
                    existing_nums_set = set()
                    for numero in existing_numeros:
                        match = re.match(r'opr-(\d+)', numero)
                        if match:
                            num = int(match.group(1))
                            if range_start <= num <= range_end:
                                existing_nums_set.add(num)
                    
                    # Trouver le prochain numéro disponible
                    for num in range(range_start, range_end + 1):
                        if num not in existing_nums_set:
                            next_available_num = num
                            break
                
                if next_available_num is None:
                    messages.error(
                        request,
                        f'Aucun numéro disponible dans la plage 1 à 99999999. '
                        f'Toutes les personnes ont déjà été créées.'
                    )
                    form = CreatePersonnesForm(request.POST)
                else:
                    # Vérifier qu'on peut créer le nombre de personnes demandé
                    end_num = next_available_num + nombre_personnes - 1
                    if end_num > range_end:
                        available_slots = range_end - next_available_num + 1
                        messages.error(
                            request,
                            f'Il ne reste que {available_slots} emplacement(s) disponible(s). '
                            f'Vous pouvez créer au maximum {available_slots} personne(s) à partir du numéro {next_available_num}.'
                        )
                        form = CreatePersonnesForm(request.POST)
                    else:
                        # Créer les personnes en masse avec bulk_create pour de meilleures performances
                        print(f"DEBUG: Debut creation en masse de {nombre_personnes} personnes")
                        try:
                            with transaction.atomic():
                                # Vérifier rapidement quelles personnes existent déjà dans la plage exacte à créer
                                numeros_to_check = [
                                    f'opr-000{next_available_num + i}'
                                    for i in range(nombre_personnes)
                                ]
                                
                                # Requête optimisée : vérifier seulement les personnes dans la plage à créer
                                already_existing_set = set(
                                    Personne.objects.filter(
                                        numero__in=numeros_to_check
                                    ).values_list('numero', flat=True)
                                )
                                
                                # Préparer tous les objets Personne en mémoire
                                # Récupérer le dernier numéro de référence valide pour générer les suivantes
                                last_ref_num = 0
                                
                                # Récupérer toutes les références qui commencent par PER-
                                all_refs = Personne.objects.filter(
                                    reference__startswith='PER-',
                                    reference__regex=r'^PER-\d+$'  # Seulement les références au format PER-XXXX (numérique)
                                ).values_list('reference', flat=True)
                                
                                # Extraire les numéros et trouver le maximum
                                for ref in all_refs:
                                    try:
                                        # Extraire le numéro après PER- (format: PER-XXXX)
                                        num_str = ref.split('-')[-1]
                                        num = int(num_str)
                                        if num > last_ref_num:
                                            last_ref_num = num
                                    except (ValueError, IndexError):
                                        # Ignorer les références au format invalide
                                        continue
                                
                                personnes_to_create = []
                                ref_counter = last_ref_num + 1
                                
                                for i in range(nombre_personnes):
                                    person_num = next_available_num + i
                                    numero = f'opr-000{person_num}'
                                    
                                    # Exclure ceux qui existent déjà
                                    if numero not in already_existing_set:
                                        # Générer la référence unique AVANT la création
                                        reference = f'PER-{str(ref_counter).zfill(4)}'
                                        
                                        personne = Personne(
                                            numero=numero,
                                            reference=reference
                                        )
                                        personnes_to_create.append(personne)
                                        ref_counter += 1
                                
                                if not personnes_to_create:
                                    messages.warning(
                                        request,
                                        f'Toutes les personnes demandées existent déjà dans la plage {next_available_num} à {next_available_num + nombre_personnes - 1}.'
                                    )
                                    return redirect('admin:inventory_personne_changelist')
                                
                                # Utiliser bulk_create avec batch_size pour optimiser les grandes insertions
                                # Les références sont déjà générées, donc pas besoin d'ignore_conflicts
                                created_personnes = Personne.objects.bulk_create(
                                    personnes_to_create,
                                    batch_size=1000
                                )
                                
                                created_count = len(created_personnes)
                                
                                if created_count > 0:
                                    first_person = next_available_num
                                    last_person = next_available_num + created_count - 1
                                    messages.success(
                                        request,
                                        f'{created_count} personne(s) créée(s) avec succès (de opr-000{first_person} à opr-000{last_person})'
                                    )
                                
                                # Si certaines personnes n'ont pas pu être créées
                                skipped = len(personnes_to_create) - created_count
                                if skipped > 0:
                                    messages.warning(
                                        request,
                                        f'{skipped} personne(s) n\'ont pas pu être créées (probablement créées entre temps par un autre processus). '
                                        f'Les personnes disponibles ont été créées avec succès.'
                                    )
                                
                                return redirect('admin:inventory_personne_changelist')
                                
                        except Exception as e:
                            # En cas d'erreur, essayer de créer les personnes une par une pour identifier le problème
                            messages.error(
                                request,
                                f'Erreur lors de la création en masse : {str(e)}. '
                                f'Tentative de création individuelle...'
                            )
                            
                            # Fallback : création individuelle pour identifier les problèmes
                            created_count = 0
                            errors = []
                            created_persons = []
                            
                            for i in range(nombre_personnes):
                                person_num = next_available_num + i
                                numero = f'opr-000{person_num}'
                                
                                if numero not in already_existing_set:
                                    try:
                                        personne = Personne(
                                            numero=numero,
                                        )
                                        personne.save()
                                        
                                        # Générer la référence
                                        if not personne.reference:
                                            personne.reference = personne.generate_reference('PER')
                                            personne.save(update_fields=['reference'])
                                        
                                        created_count += 1
                                        created_persons.append(person_num)
                                    except Exception as ex:
                                        errors.append(f'Erreur lors de la création de {numero}: {str(ex)}')
                            
                            if created_count > 0:
                                first_person = created_persons[0]
                                last_person = created_persons[-1]
                                messages.success(
                                    request,
                                    f'{created_count} personne(s) créée(s) avec succès (de opr-000{first_person} à opr-000{last_person})'
                                )
                            
                            if errors and len(errors) <= 50:
                                for error in errors:
                                    messages.warning(request, error)
                            elif errors:
                                messages.warning(
                                    request,
                                    f'{len(errors)} personne(s) n\'ont pas pu être créées. '
                                    f'Les personnes disponibles ont été créées avec succès.'
                                )
                            
                            return redirect('admin:inventory_personne_changelist')
        else:
            form = CreatePersonnesForm()
        
        # Préparer le contexte
        opts = self.model._meta
        context = {
            **self.admin_site.each_context(request),
            'opts': opts,
            'form': form,
            'title': 'Générer des personnes',
            'has_view_permission': self.has_view_permission(request),
            'has_add_permission': self.has_add_permission(request),
        }
        
        return TemplateResponse(
            request,
            'admin/inventory/personne/create_personnes.html',
            context
        )
    
    def changelist_view(self, request, extra_context=None):
        """Ajouter le bouton de création de personnes dans le changelist"""
        extra_context = extra_context or {}
        
        try:
            create_personnes_url = reverse('admin:inventory_personne_create_personnes')
        except Exception:
            create_personnes_url = '/admin/inventory/personne/create-personnes/'
        
        extra_context['create_personnes_url'] = create_personnes_url
        
        # Obtenir la réponse normale
        response = super().changelist_view(request, extra_context)
        
        # Injecter le bouton dans le HTML
        if hasattr(response, 'render') and response.status_code == 200:
            try:
                # Rendre la réponse d'abord si c'est un TemplateResponse
                response.render()
                content = response.content.decode('utf-8')
                
                # Bouton HTML à injecter
                button_html = '''
                <div style="position: fixed; top: 100px; right: 20px; z-index: 9999;">
                    <a href="''' + create_personnes_url + '''" 
                       style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                              border: none; padding: 15px 25px; color: white; text-decoration: none; 
                              border-radius: 8px; display: inline-flex; align-items: center; gap: 10px; 
                              font-size: 16px; font-weight: bold; box-shadow: 0 4px 12px rgba(17, 153, 142, 0.5);">
                        <i class="fas fa-user-plus"></i>
                        Générer des personnes
                    </a>
                </div>
                '''
                
                # Injecter avant </body>
                if '</body>' in content:
                    content = content.replace('</body>', button_html + '</body>')
                    response.content = content.encode('utf-8')
                    response['Content-Length'] = len(response.content)
                    
            except Exception as e:
                pass  # Si ça échoue, on continue normalement
        
        return response
