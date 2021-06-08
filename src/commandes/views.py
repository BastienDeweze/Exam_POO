from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.shortcuts import get_object_or_404
from articles.models import Article
from .models import Panier, ValidatedOrder, LigneCommande
from django.views.generic.edit import DeleteView
from django.views.generic.detail import DetailView
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from accounts.models import UserProfile
from eSchop.views import UserPassesTestMixinCustom
from django.db.models import Q, Max
from django.utils import timezone

from django.contrib import messages


class PanierCreate(CreateView):

    """
    CreateView créant le panier des utilisateurs.
    """

    model = Panier
    template_name = "commande/create_panier.html"
    fields = ["quantity" ]
    success_message = "Article ajouté avec succes"

    def form_valid(self, form):

        """Fonction créant ou midifiant une ligne de panier avec un article et une quantité choisie par l'utilisateur.

        Args:
            form (Form): Information necessaire à la création d'une ligne de panier

        Returns:
            HTTPResponse: L'url vers lequel l'utilisaeur sera redirigé après la création de la ligne du panier
        """

        article = get_object_or_404(Article, slug=self.kwargs['slug'])
        panier = Panier.objects.filter(user=self.request.user)
        if article.name not in [i.articles.name for i in panier]:
            form.instance.articles = article
            form.instance.user = self.request.user
            return super(PanierCreate, self).form_valid(form)
        else :
            instance = panier.get(articles=article)
            instance.quantity += form.instance.quantity
            instance.save()
            return redirect('commande:home')

class PanierHome(ListView):

    """
    ListView affichant le panier d'un utilisateur avec le total et la reduction (si il y en a).
    """

    model = Panier
    context_object_name = "panier"
    template_name = "commande/panier_list.html"

    def get_context_data(self, *args, **kwargs):

        """Fonction modifiant le context pour y ajouter le nombre d'article total, le prix total, la reduction et le nouveau prix (si il y a reduction)

        Returns:
            dict: Le nouveau context
        """

        context = super().get_context_data(*args, **kwargs)
        panier = Panier.objects.filter(user=self.request.user)
        prof = UserProfile.objects.get(user=self.request.user)
        context["price_tot"] = panier.aggregate(Sum('price'))['price__sum']
        context["nb_art_tot"] = panier.aggregate(Sum('quantity'))['quantity__sum']

        context["tot_achat"] = prof.number_of_purchase
        if context["nb_art_tot"] and context["price_tot"]:
            if (context["nb_art_tot"] + context["tot_achat"]) > prof.reduction_threshold :  
                context["sum_reduc"] = context["price_tot"] * 0.9
                context["reduc"] = "10 %"
            else:
                context["reduc"] = "Non eligible à une reduction"
                context["sum_reduc"] = context["price_tot"]
        print(type(context))
        return context

    def get_queryset(self):

        """Fonction renvoyant le panier d'un utilisateur

        Returns:
            QuerySet: Le panier de l'utilisateur.
        """

        queryset = super().get_queryset()
        return queryset.filter(user = self.request.user)


class DeletePanier(UserPassesTestMixinCustom, DeleteView):

    """
    DeleteView supprimant des lignes de panier.
    """

    model = Panier
    context_object_name = "panier"
    template_name = "commande/pannier_confirm_delete.html"
    success_url = reverse_lazy('commande:home')

    def test_func(self, *args, **kwargs):

        """Fonction verifiant que l'utilisateur faisant la requete est bien un superuser ou l'utilisateur ayant créé la ligne.

        Returns:
            bool: True si l'utilisateur est autorisé et Fase si il ne l'est pas.
        """

        return super().test_func(self, *args, **kwargs) or self.get_object() in Panier.objects.filter(user=self.request.user)

class CreateCommande(CreateView):

    """
    CreateView validant un panier et créant une commande.
    """
    
    model = Panier
    template_name = "commande/create_commande.html"
    fields = []

    def get_context_data(self, **kwargs):

        """Fonction modifiant le context pour y ajouter le nombre d'article à commander.

        Returns:
            dict: Le nouveau context
        """

        context = super().get_context_data(**kwargs)
        panier = Panier.objects.filter(user=self.request.user)
        context["nb_art_tot"] = panier.aggregate(Sum('quantity'))['quantity__sum']
        return context

    def form_valid(self, form, **kwargs):

        """Fonction créant une commande et ses lignes dans la DB

        Returns:
             HTTPResponse: L'url vers lequel l'utilisaeur sera redirigé après la validation de la commande
        """

        panier = Panier.objects.filter(user=self.request.user)
        
        if len(panier) > 0:
            userprofile = UserProfile.objects.get(user=self.request.user)

            vd = ValidatedOrder.objects.create(user=self.request.user)
            vd.tot_price_and_quantity_calculation()
            msg = ""
            for article in panier:
                lg = LigneCommande.objects.create(order=vd, article=article.articles, quantity=article.quantity)
                lg.save()
                vd.articles.add(article.articles)
                verif_stock = article.articles.set_stock(article.quantity)

                if verif_stock:
                    msg += f"{verif_stock} unité de '{article.articles.name}' dans le stock, "
            
            vd.reduction = userprofile.set_number_of_purchase(vd.tot_quantity)
            vd.save()

            Panier.objects.filter(user=self.request.user).delete()
            messages.success(self.request, "Commande Effectuée")

            if msg:
                msg = "Il manque " + msg + "l'expédition sera effectuée dès le prochain réaprovisionnement de stock"
                messages.error(self.request, msg)

        else :
            messages.error(self.request, "Vous n'avez aucun articles dans votre panier")

        return redirect('commande:home')



class UniqueCommande(CreateView):

    """
    CreateView creant une commande direct, sans passage par le panier.
    """

    model = ValidatedOrder
    template_name = "commande/create_unique_commande.html"
    fields = [ "tot_quantity" ]
    success_url = reverse_lazy('articles:home')

    def form_valid(self, form):

        """Fonction créant une commande directe et ses lignes dans la DB

        Returns:
            HTTPResponse: L'url vers lequel l'utilisaeur sera redirigé après la validation de la commande directe.
        """
        article = get_object_or_404(Article, slug=self.kwargs['slug'])
        if article :
            tot_price = article.price * form.instance.tot_quantity
            user = self.request.user
            userprofile = UserProfile.objects.get(user=user)

            vd = ValidatedOrder.objects.create(user=self.request.user, tot_price=tot_price, tot_quantity=form.instance.tot_quantity)
            lg = LigneCommande.objects.create(order=vd, article=article, quantity=form.instance.tot_quantity)
            lg.save()
            vd.articles.add(article)
            vd.reduction = userprofile.set_number_of_purchase(form.instance.tot_quantity)
            vd.save()
            verif_stock = article.set_stock(form.instance.tot_quantity)
            
            messages.success(self.request, "Commande Effectuée")
            if verif_stock:
                messages.error(self.request, f"Il manque {verif_stock} unité de '{article.name}' dans le stock, l'expédition sera effectuée dès le prochain réaprovisionnement de stock")

        else :
            messages.error(self.request, "Vous n'avez aucun articles dans votre panier")
            
        return redirect('commande:home')


class CommandeHome(UserPassesTestMixinCustom, ListView):

    """
    ListView affichant toutes les commandes du site sans exeption, reservé aux superusers.
    """

    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/validatedorder_list.html"


    def get_context_data(self, **kwargs):

        """Fonction modifiant le context pour y ajouter la quantitée max dans une commande, le prix max d'une commande et la date de la commande la plus recente.

        Returns:
            dict: Le nouveau context
        """

        context = super().get_context_data(**kwargs)
        context['max_quatity'] = ValidatedOrder.objects.all().aggregate(Max('tot_quantity'))['tot_quantity__max']
        context['max_price'] = ValidatedOrder.objects.all().aggregate(Max('tot_price'))['tot_price__max']
        context['max_date'] = ValidatedOrder.objects.all().aggregate(Max('created_on'))['created_on__max']
        
        return context

    def get_queryset(self):

        """Fonction modifiant le queryset de commandes selon la requete de l'utilisateur.
            reservé aux supperusers.

            Tri possible : par champs de recherche, par jour, par mois, par année, par quantité, par prix, par reductions, par date.

        Returns:
            QuerySet: Les commandes souhaitée trié.
        """

        queryset = super().get_queryset()
        query = self.request.GET.get('q')

        if query is not None :
            if 'q' in self.request.GET:
                return queryset.filter( Q(user__username__icontains=query)).order_by('-created_on')
        elif 'q1' in self.request.GET:
            req = self.request.GET['q1']
            if req == 'Année':
                return queryset.filter(created_on__year=timezone.now().year)
            elif req == 'Jour':
                return queryset.filter(created_on__year=timezone.now().year).filter(created_on__day=timezone.now().day).filter(created_on__month=timezone.now().month)
            elif req == 'Mois':
                return queryset.filter(created_on__year=timezone.now().year).filter(created_on__month=timezone.now().month)

        elif 'q2' in self.request.GET:
            query = self.request.GET.get('q2')
            if query == "Quantité" or query == "+Quantité":
                return self.sort_queryset(query, queryset, 'tot_quantity')

            elif query == "Prix total" or query == "+Prix total":
                return self.sort_queryset(query, queryset, 'tot_price')

            elif query == "Date" or query == "+Date":
                return self.sort_queryset(query, queryset, 'created_on')

            elif query == "Reduction" or query == "+Reduction":
                return self.sort_queryset(query, queryset, 'reduction')

        return queryset

    def sort_queryset(self, query, queryset, col):

        """Fonction ordonnant un queryset

        Args:
            query (str): La query donnée par l'utilisateur.
            queryset (QuerySet): Le queryset à ordonner.
            col (str): La colonne à ordonner

        Returns:
            QuerySet: Le queryset ordonné
        """

        if query[0] == '+' :
            return queryset.order_by(col)
        else :
            return queryset.order_by('-' + col)

class DeleteCommande(UserPassesTestMixinCustom, DeleteView):

    """
    DeleteView supprimant des commandes, reservé aux superusers.
    """

    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/validatedorder_confirm_delete.html"
    success_url = reverse_lazy('commande:stat')


class DetailCommande(UserPassesTestMixinCustom, DetailView):

    """
    DetailView affichant les detail d'une commande en particulié.
    """

    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/validatedorder_detail.html"
    success_url = reverse_lazy('commande:stat')

    def test_func(self, *args, **kwargs):

        """Redefinition de "UserPassesTestMixinCustom.test_func()" verifiant que l'utilisateur faisant la requete est bien un superuser ou l'utilisateur ayant créé la ligne.

        Returns:
            bool: True si l'utilisateur est autorisé et Fase si il ne l'est pas.
        """

        return super().test_func(self, *args, **kwargs) or self.get_object().user == self.request.user

    def get_context_data(self, *args, **kwargs):

        """Fonction modifiant le context pour y ajouter les articles de la commande demandée.

        Returns:
            dict: Le nouveau context
        """

        context = super().get_context_data(*args, **kwargs)
        context["articles"] = LigneCommande.objects.filter(order=kwargs['object'])
        return context

class MyOrders(ListView):

    """
    ListView affichant toutes les commande d'un utilisateur en particulié.
    """

    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/my_validatedorder_list.html"


    def get_queryset(self):

        """Fonction modifiant le queryset afin de retourner seulement les commande de l'utilisateur authentifié.

        Returns:
            QuerySet: Les commande de l'utilisateur connecté.
        """
        queryset = super().get_queryset().filter(user=self.request.user)

        return queryset