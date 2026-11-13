import uuid

from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.auth import ip_da_requisicao
from core.api.permissions import (
    EscopoDoTCC,
    GestaoDePessoas,
    LeituraOuAdministrador,
    LeituraOuGestao,
    ProfessorTccOuAdministrador,
)
from core.api.serializers import (
    AcessoExternoSerializer,
    AgendarReuniaoSerializer,
    AlunoEntradaSerializer,
    AlunoSerializer,
    AreaConhecimentoSerializer,
    BancaSerializer,
    CadastrarBancaSerializer,
    ConvidarAudienciaSerializer,
    ConviteRecebidoSerializer,
    ConviteSerializer,
    CursoSerializer,
    DocenteEntradaSerializer,
    DocenteSerializer,
    EnviarSolicitacaoSerializer,
    MembroExternoEntradaSerializer,
    MudarSituacaoSerializer,
    OrientadorSerializer,
    RegistrarPublicacaoSerializer,
    ResponderConviteSerializer,
    ResponderPorLinkSerializer,
    ResponderSolicitacaoSerializer,
    ReuniaoSerializer,
    SolicitacaoOrientacaoSerializer,
    TCCDetalheSerializer,
    TCCSerializer,
    UsuarioEntradaSerializer,
    UsuarioSerializer,
)
from core.models import (
    TCC,
    Aluno,
    AreaConhecimento,
    Banca,
    Convite,
    Curso,
    Docente,
    HistoricoStatus,
    ParticipacaoBanca,
    ReuniaoAlinhamento,
    SolicitacaoOrientacao,
    TipoUsuario,
    Usuario,
)
from core.services import acesso_externo as servico_acesso_externo
from core.services import banca as servico_banca
from core.services import contas as servico_contas
from core.services import convites as servico_convites
from core.services import docente as servico_docente
from core.services import escopo
from core.services import pessoas as servico_pessoas
from core.services import publicacao as servico_publicacao
from core.services import reuniao as servico_reuniao
from core.services import solicitacao as servico_solicitacao
from core.services import tcc as servico_tcc


class TCCViewSet(viewsets.ModelViewSet):
    """/api/tccs/ (B7a) e /api/tccs/{id}/situacao/ (B7b).

    Filtros da listagem (B9b): ?busca= (titulo, autor, orientador), ?curso=<id>,
    ?status=, ?modalidade= e ?ativo=true|false.

    Visao por perfil (C17): a listagem so traz os TCCs do escopo do usuario; abrir
    ou alterar um TCC fora dele devolve 403 e fica registrado (EscopoDoTCC).
    """

    serializer_class = TCCSerializer
    permission_classes = [LeituraOuGestao, EscopoDoTCC]
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
            qs = qs.prefetch_related(
                Prefetch(
                    "historico_status",
                    queryset=HistoricoStatus.objects.select_related("alterado_por"),
                )
            )
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
        if self.action == "list":
            # No detalhe o TCC fora do escopo nao some (404): e recusado com 403
            # e registrado pela EscopoDoTCC.
            qs = escopo.filtrar_tccs_visiveis(self.request.user, qs)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TCCDetalheSerializer
        return TCCSerializer

    def perform_create(self, serializer):
        orientador = serializer.validated_data["orientador"]
        if not escopo.pode_cadastrar_tcc_para(self.request.user, orientador):
            raise PermissionDenied(
                "Só o próprio orientador ou o Professor de TCC cadastra o TCC."
            )
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
        self.get_object()  # 404 ou 403 (escopo) antes de validar a entrada
        entrada = MudarSituacaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        tcc = servico_tcc.mudar_situacao(
            tcc_id=pk, usuario=request.user, **entrada.validated_data
        )
        return Response(
            TCCDetalheSerializer(tcc, context=self.get_serializer_context()).data
        )

    @action(detail=True, methods=["post"])
    def publicacao(self, request, pk=None):
        """C1: registra a publicacao e aprova o TCC por publicacao, de uma vez."""
        self.get_object()  # 404 ou 403 (escopo) antes de validar a entrada
        entrada = RegistrarPublicacaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        tcc = servico_publicacao.registrar_publicacao(
            tcc_id=pk, dados=entrada.validated_data, usuario=request.user
        )
        return Response(
            TCCDetalheSerializer(tcc, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class BancaViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/bancas/ (B8): listar, detalhar e cadastrar (local pelo DER v2, C9).

    Visao por perfil (C17): cada um ve as bancas dos TCCs do seu escopo e as
    bancas de que participa; so quem edita o TCC cadastra a banca dele.
    """

    serializer_class = BancaSerializer
    permission_classes = [LeituraOuGestao]

    def get_queryset(self):
        usuario = self.request.user
        visiveis = escopo.filtrar_tccs_visiveis(usuario, TCC.objects.all())
        participa = ParticipacaoBanca.objects.filter(
            banca=OuterRef("pk"), usuario=usuario
        )
        return (
            Banca.objects.filter(
                Q(tcc_id__in=visiveis.values("pk")) | Q(Exists(participa))
            )
            .select_related("tcc")
            .prefetch_related("participacoes__usuario", "convites")
            .order_by("data_hora_inicio")
        )

    @action(detail=True, methods=["post"])
    def audiencia(self, request, pk=None):
        """C6 (PF34): convida, por pessoa, docentes e alunos para assistir."""
        banca = self.get_object()
        entrada = ConvidarAudienciaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        servico_convites.convidar_audiencia(
            banca=banca, usuario=request.user, **entrada.validated_data
        )
        banca = self.get_queryset().get(pk=banca.pk)
        return Response(BancaSerializer(banca).data, status=status.HTTP_201_CREATED)

    def create(self, request):
        entrada = CadastrarBancaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        tcc = entrada.validated_data["tcc"]
        if not escopo.pode_editar_tcc(request.user, tcc):
            escopo.registrar_acesso_negado(request.user, tcc, "POST cadastrar banca")
            raise PermissionDenied(EscopoDoTCC.message)
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
                Q(usuario__nome_completo__icontains=busca)
                | Q(matricula__icontains=busca)
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
            usuario_id=pk,
            ativo=False,
            usuario=request.user,
            entidade=conta.tipo_usuario,
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


# ------------------------------------------- C3a: orientacao academica (7.2)
def _docentes_com_carga():
    """Docentes com a carga de orientacao (RD17) anotada em qtd_orientacoes."""
    return Docente.objects.select_related("usuario").annotate(
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
    )


class OrientadorViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/orientadores/ (PF63): busca de orientador por area e nome.

    Lista so docentes ativos, com as areas de interesse e o numero de
    orientandos. Filtros: ?area=<id> e ?busca=<nome>.
    """

    serializer_class = OrientadorSerializer

    def get_queryset(self):
        qs = (
            _docentes_com_carga()
            .filter(usuario__ativo=True)
            .prefetch_related("areas_interesse")
            .order_by("-aceita_orientacoes", "usuario__nome_completo")
        )
        params = self.request.query_params
        if params.get("area"):
            qs = filtro_uuid(qs, "areas_interesse__id", params["area"]).distinct()
        if params.get("busca"):
            qs = qs.filter(usuario__nome_completo__icontains=params["busca"])
        return qs


class SolicitacaoOrientacaoViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/solicitacoes-orientacao/ (PF41 a PF43).

    O aluno envia (POST) e ve as que enviou; o docente ve as que recebeu e
    responde em /{id}/responder/. Filtro: ?status=.
    """

    serializer_class = SolicitacaoOrientacaoSerializer

    def get_queryset(self):
        qs = SolicitacaoOrientacao.objects.select_related(
            "aluno__usuario", "aluno__curso", "docente__usuario", "reuniao"
        ).order_by("-enviada_em")
        qs = servico_solicitacao.filtrar_visiveis(self.request.user, qs)
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs

    def create(self, request):
        aluno = getattr(request.user, "aluno", None)
        if aluno is None:
            raise PermissionDenied("Só o aluno solicita orientação.")
        entrada = EnviarSolicitacaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        solicitacao = servico_solicitacao.enviar_solicitacao(
            aluno=aluno, usuario=request.user, **entrada.validated_data
        )
        return Response(
            self.get_serializer(solicitacao).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def responder(self, request, pk=None):
        entrada = ResponderSolicitacaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        solicitacao = servico_solicitacao.responder_solicitacao(
            solicitacao_id=pk, usuario=request.user, **entrada.validated_data
        )
        return Response(self.get_serializer(solicitacao).data)

    @action(detail=True, methods=["post"])
    def reuniao(self, request, pk=None):
        """C3b (PF44): agenda ou remarca a reuniao; devolve os alertas de agenda."""
        entrada = AgendarReuniaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        reuniao, criada, alertas = servico_reuniao.agendar_reuniao(
            solicitacao_id=pk, usuario=request.user, **entrada.validated_data
        )
        return Response(
            {"reuniao": ReuniaoSerializer(reuniao).data, "alertas": alertas},
            status=status.HTTP_201_CREATED if criada else status.HTTP_200_OK,
        )


class ReuniaoViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/reunioes/ (C3b, PF45): reunioes de alinhamento de quem consulta.

    ?futuras=true traz so as que ainda vao acontecer.
    """

    serializer_class = ReuniaoSerializer

    def get_queryset(self):
        qs = ReuniaoAlinhamento.objects.select_related(
            "solicitacao__aluno__usuario", "solicitacao__docente__usuario"
        ).order_by("data_hora")
        qs = servico_reuniao.filtrar_reunioes_visiveis(self.request.user, qs)
        if self.request.query_params.get("futuras") == "true":
            qs = qs.filter(data_hora__gte=timezone.now())
        return qs


# ---------------------------------------- C6: convites de banca e audiencia
class ConviteViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/convites/ (PF62): convites recebidos por quem consulta.

    /{id}/responder/ aceita ou recusa (PF35); /{id}/reenviar/ reenvia um
    pendente (PF33, quem edita o TCC); /link/ e a rota publica do link do
    e-mail, usada pelo membro externo (sem login).
    """

    serializer_class = ConviteRecebidoSerializer

    def get_queryset(self):
        qs = (
            Convite.objects.filter(usuario=self.request.user)
            .select_related(*servico_convites.RELACIONADOS)
            .order_by("-enviado_em")
        )
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs

    @action(detail=True, methods=["post"])
    def responder(self, request, pk=None):
        entrada = ResponderConviteSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        convite = servico_convites.responder_como_usuario(
            convite_id=pk, usuario=request.user, **entrada.validated_data
        )
        return Response(ConviteRecebidoSerializer(convite).data)

    @action(detail=True, methods=["post"])
    def reenviar(self, request, pk=None):
        convite = servico_convites.reenviar_convite(convite_id=pk, usuario=request.user)
        return Response(ConviteSerializer(convite).data)

    @action(
        detail=False,
        methods=["get", "post"],
        permission_classes=[AllowAny],
        authentication_classes=[],
    )
    def link(self, request):
        if request.method == "GET":
            convite = servico_convites.convite_por_assinatura(
                request.query_params.get("c")
            )
            return Response(ConviteRecebidoSerializer(convite).data)
        entrada = ResponderPorLinkSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        convite = servico_convites.responder_por_link(
            valor_assinatura=entrada.validated_data["c"],
            resposta=entrada.validated_data["resposta"],
        )
        return Response(ConviteRecebidoSerializer(convite).data)


# ------------------------------------ C16: acesso temporario do externo (4.6)
class MembroExternoView(APIView):
    """POST /api/membros-externos/ (PF60): Professor de TCC ou administrador
    cadastra o membro externo, sem senha (ele entra so pelo token)."""

    permission_classes = [ProfessorTccOuAdministrador]

    def post(self, request):
        entrada = MembroExternoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        conta = servico_pessoas.cadastrar_usuario(
            dados={
                **entrada.validated_data,
                "tipo_usuario": TipoUsuario.MEMBRO_EXTERNO,
            },
            usuario=request.user,
        )
        return Response(UsuarioSerializer(conta).data, status=status.HTTP_201_CREATED)


class AcessoExternoView(APIView):
    """GET /api/acesso-externo/<token>/ (PF19): leitura do TCC pelo membro
    externo, sem login, ate 48 h depois da defesa (RD32)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, token):
        acesso = servico_acesso_externo.validar_token(token)
        servico_acesso_externo.registrar_acesso(acesso, ip_da_requisicao(request))
        return Response(AcessoExternoSerializer(acesso).data)
