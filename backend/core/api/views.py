import uuid

from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api.permissions import (
    GestaoDePessoas,
    LeituraOuAdministrador,
    LeituraOuGestao,
)
from core.api.serializers import (
    AlunoEntradaSerializer,
    AlunoSerializer,
    AreaConhecimentoSerializer,
    BancaSerializer,
    CadastrarBancaSerializer,
    CursoSerializer,
    DocenteEntradaSerializer,
    DocenteSerializer,
    MudarSituacaoSerializer,
    TCCDetalheSerializer,
    TCCSerializer,
    UsuarioEntradaSerializer,
    UsuarioSerializer,
)
from core.models import TCC, Aluno, AreaConhecimento, Banca, Curso, Docente, Usuario
from core.services import banca as servico_banca
from core.services import contas as servico_contas
from core.services import docente as servico_docente
from core.services import pessoas as servico_pessoas
from core.services import tcc as servico_tcc


class TCCViewSet(viewsets.ModelViewSet):
    """/api/tccs/ (B7a) e /api/tccs/{id}/situacao/ (B7b).

    Filtros da listagem (B9b): ?busca= (titulo, autor, orientador), ?curso=<id>,
    ?status=, ?modalidade= e ?ativo=true|false.
    """

    serializer_class = TCCSerializer
    permission_classes = [LeituraOuGestao]
    # Sem DELETE: TCC nao se apaga, e inativado com motivo (RD13)
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = TCC.objects.select_related(
            "curso",
            "area_conhecimento",
            "autor__usuario",
            "orientador__usuario",
            "coorientador__usuario",
        ).order_by("-data_cadastro")
        if self.action == "retrieve":
            qs = qs.prefetch_related("historico_status")
        params = self.request.query_params
        qs = filtro_ativo(qs, self.request, "ativo")
        busca = params.get("busca")
        if busca:
            qs = qs.filter(
                Q(titulo__icontains=busca)
                | Q(autor__usuario__nome_completo__icontains=busca)
                | Q(orientador__usuario__nome_completo__icontains=busca)
            )
        for campo in ("status", "modalidade"):
            if params.get(campo):
                qs = qs.filter(**{campo: params[campo]})
        if params.get("curso"):
            qs = filtro_uuid(qs, "curso_id", params["curso"])
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TCCDetalheSerializer
        return TCCSerializer

    def perform_create(self, serializer):
        serializer.instance = servico_tcc.cadastrar_tcc(
            dados=serializer.validated_data, usuario=self.request.user
        )

    def perform_update(self, serializer):
        serializer.instance = servico_tcc.atualizar_tcc(
            tcc_id=serializer.instance.pk,
            dados=serializer.validated_data,
            usuario=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def situacao(self, request, pk=None):
        entrada = MudarSituacaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        tcc = servico_tcc.mudar_situacao(
            tcc_id=pk, usuario=request.user, **entrada.validated_data
        )
        return Response(TCCDetalheSerializer(tcc).data)


class BancaViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/bancas/ (B8): listar, detalhar e cadastrar."""

    queryset = Banca.objects.prefetch_related("participacoes").order_by("data_hora")
    serializer_class = BancaSerializer
    permission_classes = [LeituraOuGestao]

    def create(self, request):
        entrada = CadastrarBancaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        banca = servico_banca.cadastrar_banca(
            usuario=request.user, **entrada.validated_data
        )
        return Response(BancaSerializer(banca).data, status=status.HTTP_201_CREATED)


def filtro_uuid(queryset, campo, valor):
    """Filtra por id; um id mal formado devolve lista vazia em vez de erro 500."""
    try:
        return queryset.filter(**{campo: uuid.UUID(str(valor))})
    except ValueError:
        return queryset.none()


def filtro_ativo(queryset, request, campo):
    """?ativo=true|false filtra pela conta; sem o parametro, traz todos."""
    valor = request.query_params.get("ativo")
    if valor in ("true", "false"):
        return queryset.filter(**{campo: valor == "true"})
    return queryset


class DocenteViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/docentes/ (B6): todos leem; so o administrador cadastra e edita."""

    serializer_class = DocenteSerializer
    permission_classes = [LeituraOuAdministrador]

    def get_queryset(self):
        qs = (
            Docente.objects.select_related("usuario")
            .prefetch_related("areas_interesse")
            .annotate(
                # RBN15: orientacoes e coorientacoes de TCC ativos
                qtd_orientacoes=Count(
                    "tccs_orientados",
                    filter=Q(tccs_orientados__ativo=True),
                    distinct=True,
                )
                + Count(
                    "tccs_coorientados",
                    filter=Q(tccs_coorientados__ativo=True),
                    distinct=True,
                ),
                # RBN16: bancas como titular ou suplente
                qtd_bancas=Count("usuario__participacoes_banca", distinct=True),
            )
            .order_by("usuario__nome_completo")
        )
        qs = filtro_ativo(qs, self.request, "usuario__ativo")
        busca = self.request.query_params.get("busca")
        if busca:
            qs = qs.filter(
                Q(usuario__nome_completo__icontains=busca)
                | Q(matricula_institucional__icontains=busca)
            )
        return qs

    def _saida(self, pk):
        return DocenteSerializer(self.get_queryset().get(pk=pk)).data

    def create(self, request):
        entrada = DocenteEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        docente = servico_docente.cadastrar_docente(
            dados=entrada.validated_data, usuario=request.user
        )
        return Response(self._saida(docente.pk), status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        entrada = DocenteEntradaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        docente = servico_docente.atualizar_docente(
            docente_id=pk, dados=entrada.validated_data, usuario=request.user
        )
        return Response(self._saida(docente.pk))

    @action(detail=True, methods=["post"])
    def desativar(self, request, pk=None):
        self.get_object()  # 404 se o id nao for de um docente
        conta = servico_contas.alterar_ativo(
            usuario_id=pk, ativo=False, usuario=request.user, entidade="DOCENTE"
        )
        return Response(self._saida(conta.pk))

    @action(detail=True, methods=["post"])
    def reativar(self, request, pk=None):
        self.get_object()  # 404 se o id nao for de um docente
        conta = servico_contas.alterar_ativo(
            usuario_id=pk, ativo=True, usuario=request.user, entidade="DOCENTE"
        )
        return Response(self._saida(conta.pk))


class AlunoViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/alunos/ (B14): o administrador cadastra; docentes consultam."""

    serializer_class = AlunoSerializer
    permission_classes = [GestaoDePessoas]

    def get_queryset(self):
        qs = Aluno.objects.select_related("usuario", "curso").order_by(
            "usuario__nome_completo"
        )
        qs = filtro_ativo(qs, self.request, "usuario__ativo")
        busca = self.request.query_params.get("busca")
        if busca:
            qs = qs.filter(
                Q(usuario__nome_completo__icontains=busca) | Q(matricula__icontains=busca)
            )
        curso = self.request.query_params.get("curso")
        if curso:
            qs = filtro_uuid(qs, "curso_id", curso)
        return qs

    def _saida(self, pk):
        return AlunoSerializer(self.get_queryset().get(pk=pk)).data

    def create(self, request):
        entrada = AlunoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        aluno = servico_pessoas.cadastrar_aluno(
            dados=entrada.validated_data, usuario=request.user
        )
        return Response(self._saida(aluno.pk), status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        entrada = AlunoEntradaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        aluno = servico_pessoas.atualizar_aluno(
            aluno_id=pk, dados=entrada.validated_data, usuario=request.user
        )
        return Response(self._saida(aluno.pk))

    @action(detail=True, methods=["post"])
    def desativar(self, request, pk=None):
        self.get_object()
        servico_contas.alterar_ativo(
            usuario_id=pk, ativo=False, usuario=request.user, entidade="ALUNO"
        )
        return Response(self._saida(pk))

    @action(detail=True, methods=["post"])
    def reativar(self, request, pk=None):
        self.get_object()
        servico_contas.alterar_ativo(
            usuario_id=pk, ativo=True, usuario=request.user, entidade="ALUNO"
        )
        return Response(self._saida(pk))


class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/usuarios/ (B14): secretaria, administrador e membro externo.

    ?tipo=MEMBRO_EXTERNO lista quem pode compor banca alem dos docentes.
    """

    serializer_class = UsuarioSerializer
    permission_classes = [GestaoDePessoas]

    def get_queryset(self):
        qs = (
            Usuario.objects.filter(tipo_usuario__in=servico_pessoas.TIPOS_GERAIS)
            .select_related("membro_externo")
            .order_by("nome_completo")
        )
        qs = filtro_ativo(qs, self.request, "ativo")
        tipo = self.request.query_params.get("tipo")
        if tipo:
            qs = qs.filter(tipo_usuario=tipo)
        return qs

    def _saida(self, pk):
        return UsuarioSerializer(self.get_queryset().get(pk=pk)).data

    def create(self, request):
        entrada = UsuarioEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        conta = servico_pessoas.cadastrar_usuario(
            dados=entrada.validated_data, usuario=request.user
        )
        return Response(self._saida(conta.pk), status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        entrada = UsuarioEntradaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        conta = servico_pessoas.atualizar_usuario(
            usuario_id=pk, dados=entrada.validated_data, usuario=request.user
        )
        return Response(self._saida(conta.pk))

    @action(detail=True, methods=["post"])
    def desativar(self, request, pk=None):
        conta = self.get_object()
        servico_contas.alterar_ativo(
            usuario_id=pk, ativo=False, usuario=request.user, entidade=conta.tipo_usuario
        )
        return Response(self._saida(pk))

    @action(detail=True, methods=["post"])
    def reativar(self, request, pk=None):
        conta = self.get_object()
        servico_contas.alterar_ativo(
            usuario_id=pk, ativo=True, usuario=request.user, entidade=conta.tipo_usuario
        )
        return Response(self._saida(pk))


class CursoViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/cursos/: os tres cursos do NUCOMP (semeados pela migration 0002)."""

    queryset = Curso.objects.order_by("nome")
    serializer_class = CursoSerializer


class AreaConhecimentoViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/areas/: lista para todos; so o administrador cadastra."""

    queryset = AreaConhecimento.objects.order_by("nome")
    serializer_class = AreaConhecimentoSerializer
    permission_classes = [LeituraOuAdministrador]

    def create(self, request):
        entrada = AreaConhecimentoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        area = servico_pessoas.cadastrar_area(
            nome=entrada.validated_data["nome"], usuario=request.user
        )
        return Response(
            AreaConhecimentoSerializer(area).data, status=status.HTTP_201_CREATED
        )
