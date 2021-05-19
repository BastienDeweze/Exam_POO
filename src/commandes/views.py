from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.shortcuts import get_object_or_404
from articles.models import Article
from .models import Panier, ValidatedOrder, LigneCommande
from django.views.generic.edit import DeleteView
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from accounts.models import UserProfile
from django.contrib.auth.mixins import UserPassesTestMixin

# Create your views here.

class PanierCreate(CreateView):
    model = Panier
    template_name = "commande/create_panier.html"
    fields = ["quantity" ]
    success_message = "Article ajouté avec succes"

    def form_valid(self, form):
        article = get_object_or_404(Article, slug=self.kwargs['slug'])
        panier = Panier.objects.filter(user=self.request.user)
        if article.name not in [i.articles.name for i in panier]:
            form.instance.articles = article
            form.instance.user = self.request.user
            print("ici")
            return super(PanierCreate, self).form_valid(form)
        else :
            print(panier.get(articles=article))
            instance = panier.get(articles=article)
            instance.quantity += form.instance.quantity
            instance.save()
            return redirect('commande:home')

class PanierHome(ListView):
    model = Panier
    context_object_name = "panier"
    template_name = "commande/panier_list.html"

    def get_context_data(self, *args, **kwargs):
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
        return context

    def get_queryset(self):

        queryset = super().get_queryset()
        return queryset.filter(user = self.request.user)

class DeletePanier(UserPassesTestMixin, DeleteView):
    model = Panier
    context_object_name = "panier"
    template_name = "commande/pannier_confirm_delete.html"

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        print(self.object)
        print(self.request.user)
        Panier.objects.filter(user=self.request.user).delete()
        print(self.kwargs)
        return redirect('commande:home')

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser or self.get_object() in Panier.objects.filter(user=self.request.user)

class CreateCommande(CreateView):
    model = Panier
    template_name = "commande/create_commande.html"
    fields = []

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        panier = Panier.objects.filter(user=self.request.user)
        prof = UserProfile.objects.get(user=self.request.user)
        context["price_tot"] = panier.aggregate(Sum('price'))['price__sum']
        context["nb_art_tot"] = panier.aggregate(Sum('quantity'))['quantity__sum']

        context["tot_achat"] = prof.number_of_purchase
        print(context["nb_art_tot"])
        print(context["tot_achat"])
        if context["nb_art_tot"] and context["price_tot"]:
            if (context["nb_art_tot"] + context["tot_achat"]) > prof.reduction_threshold :
                context["sum_reduc"] = context["price_tot"] * 0.9
                context["reduc"] = "10 %"
            else:
                context["reduc"] = "Non eligible à une reduction"
                context["sum_reduc"] = context["price_tot"]
        #print(context)
        return context

    def form_valid(self, form, **kwargs):
        panier = Panier.objects.filter(user=self.request.user)
        if len(panier) > 0:
            user = self.request.user
            tot_price = panier.aggregate(Sum('price'))['price__sum']
            tot_quantity = panier.aggregate(Sum('quantity'))['quantity__sum']
            vd = ValidatedOrder.objects.create(user=self.request.user, tot_price=tot_price, tot_quantity=tot_quantity)
            vd.save()
            for article in panier:
                lg = LigneCommande.objects.create(order=vd, article=article.articles, quantity=article.quantity)
                lg.save()
                vd.articles.add(article.articles)
            vd.reduction = self.modif_number_of_purchase(user, tot_quantity)
            vd.save()
            Panier.objects.filter(user=self.request.user).delete()

        return redirect('commande:home')


    def modif_number_of_purchase(self, user, nb):
        us = UserProfile.objects.get(user=user)
        us.total_number_of_purchase += nb
        if us.number_of_purchase + nb > us.reduction_threshold :
            us.number_of_purchase = 0
        else:
            us.number_of_purchase += nb
        us.save()
        return us.number_of_purchase == 0


class UniqueCommande(CreateView):
    model = ValidatedOrder
    template_name = "commande/create_unique_commande.html"
    fields = [ "tot_quantity" ]
    success_url = reverse_lazy('articles:home')

    def form_valid(self, form):
        article = get_object_or_404(Article, slug=self.kwargs['slug'])
        if article :
            tot_price = article.price * form.instance.tot_quantity
            user = self.request.user

            vd = ValidatedOrder.objects.create(user=self.request.user, tot_price=tot_price, tot_quantity=form.instance.tot_quantity)
            vd.save()
            lg = LigneCommande.objects.create(order=vd, article=article, quantity=form.instance.tot_quantity)
            lg.save()
            vd.articles.add(article)
            vd.reduction = self.modif_number_of_purchase(user, form.instance.tot_quantity)
            vd.save()
            
        return redirect('commande:home')

    def modif_number_of_purchase(self, user, nb):
        us = UserProfile.objects.get(user=user)
        us.total_number_of_purchase += nb
        if us.number_of_purchase + nb > us.reduction_threshold :
            us.number_of_purchase = 0
        else:
            us.number_of_purchase += nb
        us.save()
        return us.number_of_purchase == 0

class CommandeHome(ListView):
    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/validatedorder_list.html"