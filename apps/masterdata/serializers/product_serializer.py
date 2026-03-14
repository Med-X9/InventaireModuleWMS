from rest_framework import serializers
from ..models import Product, NSerie, Family, Location
from django.utils.translation import gettext_lazy as _

class NSerieSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les numéros de série
    """
    product_reference = serializers.CharField(source='product.reference', read_only=True)
    product_name = serializers.CharField(source='product.Short_Description', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_warranty_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = NSerie
        fields = [
            'id', 'reference', 'n_serie', 'product', 'product_reference', 'product_name',
            'status', 'description', 'date_fabrication', 'date_expiration', 'warranty_end_date',
            'is_expired', 'is_warranty_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reference', 'created_at', 'updated_at']

class NSerieCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création de numéros de série
    """
    class Meta:
        model = NSerie
        fields = [
            'n_serie', 'product', 'status', 'description', 'date_fabrication',
            'date_expiration', 'warranty_end_date'
        ]
    
    def validate(self, data):
        """
        Validation personnalisée
        """
        # Vérifier que le produit supporte les numéros de série
        product = data.get('product')
        if product and not product.n_serie:
            raise serializers.ValidationError(_('Ce produit ne supporte pas les numéros de série'))
        
        # Vérifier l'unicité du numéro de série pour ce produit
        n_serie = data.get('n_serie')
        if n_serie and product:
            if NSerie.objects.filter(n_serie=n_serie, product=product).exists():
                raise serializers.ValidationError(_('Ce numéro de série existe déjà pour ce produit'))
        
        return data

class NSerieUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour de numéros de série
    """
    class Meta:
        model = NSerie
        fields = [
            'status', 'description', 'date_fabrication', 'date_expiration',
            'warranty_end_date'
        ]
    
    def validate(self, data):
        """
        Validation personnalisée pour la mise à jour
        """
        instance = self.instance
        if instance:
            # Vérifier que le produit supporte toujours les numéros de série
            if not instance.product.n_serie:
                raise serializers.ValidationError(_('Ce produit ne supporte pas les numéros de série'))
        
        return data

class ProductNSerieSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les produits avec leurs numéros de série
    """
    numeros_serie = NSerieSerializer(many=True, read_only=True)
    numeros_serie_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'reference', 'Internal_Product_Code', 'Short_Description',
            'Barcode', 'Product_Group', 'Stock_Unit', 'Product_Status',
            'Product_Family', 'Is_Variant', 'n_lot', 'n_serie', 'dlc',
            'parent_product', 'numeros_serie', 'numeros_serie_count'
        ]
    
    def get_numeros_serie_count(self, obj):
        """
        Retourne le nombre de numéros de série pour ce produit
        """
        return obj.numeros_serie.count()

class NSerieListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la liste des numéros de série avec informations de base
    """
    product_reference = serializers.CharField(source='product.reference', read_only=True)
    product_name = serializers.CharField(source='product.Short_Description', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_warranty_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = NSerie
        fields = [
            'id', 'reference', 'n_serie', 'product_reference', 'product_name',
            'status', 'is_expired', 'is_warranty_valid', 'created_at'
        ]

class NSerieDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour les numéros de série
    """
    product = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    is_warranty_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = NSerie
        fields = [
            'id', 'reference', 'n_serie', 'product', 'status', 'description',
            'date_fabrication', 'date_expiration', 'warranty_end_date',
            'is_expired', 'is_warranty_valid', 'created_at', 'updated_at'
        ]
    
    def get_product(self, obj):
        """
        Retourne les informations du produit
        """
        return {
            'id': obj.product.id,
            'reference': obj.product.reference,
            'internal_code': obj.product.Internal_Product_Code,
            'name': obj.product.Short_Description,
            'barcode': obj.product.Barcode,
            'family': obj.product.Product_Family.family_name if obj.product.Product_Family else None
        }
    