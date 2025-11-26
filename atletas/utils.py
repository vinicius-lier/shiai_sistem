from datetime import date
from django.db.models import Q
    hoje = date.today()
    idade = hoje.year - ano_nasc
    
    if idade <= 6:
        return "Festival"
    elif idade <= 8:
        return "SUB 9"
    elif idade <= 10:
        return "SUB 11"
    elif idade <= 12:
        return "SUB 13"
    elif idade <= 14:
        return "SUB 15"
    elif idade <= 17:
        return "SUB 18"
    elif idade <= 20:
        return "SUB 21"
    else:
        return "SÊNIOR"


    categoria_atual = Categoria.objects.filter(
        classe=atleta.classe,
        sexo=atleta.sexo,
        categoria_nome=atleta.categoria_nome
    ).first()
    
    if not categoria_atual:
    
    # Verifica se peso está dentro dos limites (limite_max pode ser 999.0 para categorias "acima de")
    limite_max_real = categoria_atual.limite_max if categoria_atual.limite_max < 999.0 else 999999.0
    
    if categoria_atual.limite_min <= peso_oficial <= limite_max_real:
            limite_min__gt=limite_max_real
        ).exclude(limite_max__gte=999.0).order_by('limite_min').first()
        
        if not categoria_superior:
                limite_min__lte=peso_oficial,
                limite_max__gte=999.0
            ).order_by('-limite_min').first()
        
        if categoria_superior:
    
    # Peso abaixo do limite mínimo - buscar categoria correta que contenha o peso
    if peso_oficial < categoria_atual.limite_min:
        # Buscar categoria que contenha o peso do atleta
        limite_max_real = categoria_atual.limite_max if categoria_atual.limite_max < 999.0 else 999999.0
        
        # Primeiro tentar encontrar categoria que contenha o peso exato
        categoria_correta = Categoria.objects.filter(
            classe=atleta.classe,
            sexo=atleta.sexo,
            limite_min__lte=peso_oficial
        ).exclude(
            categoria_nome=categoria_atual.categoria_nome  # Excluir a categoria atual
        )
        
        # Filtrar categorias normais (com limite_max < 999.0)
        categorias_normais = categoria_correta.filter(limite_max__lt=999.0)
        
        if categorias_normais.exists():
            # Buscar categoria que contenha o peso (limite_min <= peso <= limite_max)
            categoria_que_contem = categorias_normais.filter(limite_max__gte=peso_oficial).order_by('limite_min').first()
            if categoria_que_contem:
                atleta.motivo_ajuste = f"Peso {peso_oficial}kg abaixo do limite mínimo da categoria atual ({categoria_atual.limite_min}kg). Categoria correta: {categoria_que_contem.categoria_nome}"
                return categoria_que_contem, "Pode rebaixar para categoria inferior"
            
            # Se não encontrou categoria que contenha, buscar a categoria com limite_max mais próximo e menor que o peso
            categoria_inferior = categorias_normais.filter(limite_max__lt=peso_oficial).order_by('-limite_max').first()
            if categoria_inferior:
                atleta.motivo_ajuste = f"Peso {peso_oficial}kg abaixo do limite mínimo ({categoria_atual.limite_min}kg) - Pode rebaixar"
                return categoria_inferior, "Pode rebaixar para categoria inferior"
        
        # Verificar categoria "acima de" (Super Pesado)
        categoria_acima = categoria_correta.filter(limite_max__gte=999.0).order_by('-limite_min').first()
        if categoria_acima and categoria_acima.limite_min <= peso_oficial:
            atleta.motivo_ajuste = f"Peso {peso_oficial}kg abaixo do limite mínimo ({categoria_atual.limite_min}kg). Categoria correta: {categoria_acima.categoria_nome}"
            return categoria_acima, "Pode rebaixar para categoria inferior"
        
        # Não encontrou categoria apropriada
        atleta.status = "Eliminado Peso"
        atleta.motivo_ajuste = f"Peso {peso_oficial}kg abaixo da primeira categoria disponível"
        return None, "Eliminado - Peso abaixo da primeira categoria"
    
    return categoria_atual, "OK"


        classe=classe,
        sexo=sexo,
        categoria=categoria_nome,
        defaults={'estrutura': {}}
    )
    
    # Limpar lutas antigas e atletas
    chave.lutas.all().delete()
    chave.atletas.clear()
    chave.atletas.set(atletas_list)
    
    
    chave.estrutura = estrutura
    chave.save()
    
    return chave


    num_atletas = len(atletas_list)
    
    # Calcular próximo tamanho de chave (4, 8, 16...)
    if num_atletas <= 4:
        tamanho_chave = 4
    elif num_atletas <= 8:
        tamanho_chave = 8
    elif num_atletas <= 16:
        tamanho_chave = 16
    else:
        tamanho_chave = 32
    
    
    estrutura = {
        "tipo": "chave_olimpica",
        "atletas": num_atletas,
        "tamanho_chave": tamanho_chave,
        "rounds": {}
    }
    
    # Criar lutas do primeiro round
    round_num = 1
    lutas_round = []
    num_lutas = tamanho_chave // 2
    
    for i in range(0, tamanho_chave, 2):
        
        # Se um dos atletas existe, criar luta
        if atleta_a or atleta_b:
            luta = Luta.objects.create(
                chave=chave,
                atleta_a=atleta_a,
                atleta_b=atleta_b,
                round=round_num,
                proxima_luta=None  # Será definido depois
            )
            lutas_round.append(luta.id)
    
    estrutura["rounds"][round_num] = lutas_round
    
    # Criar lutas dos rounds seguintes e vincular
    lutas_anteriores = lutas_round
    while len(lutas_anteriores) > 1:
        round_num += 1
        num_lutas = len(lutas_anteriores) // 2
        lutas_novo_round = []
        
        for i in range(num_lutas):
            luta = Luta.objects.create(
                chave=chave,
                atleta_a=None,  # Será preenchido quando a luta anterior terminar
                atleta_b=None,
                round=round_num,
                proxima_luta=None  # Será definido depois
            )
            lutas_novo_round.append(luta.id)
        
        # Vincular lutas do round anterior às do novo round
        for idx, luta_ant_id in enumerate(lutas_anteriores):
            try:
                luta_ant = Luta.objects.get(id=luta_ant_id)
                proxima_luta_idx = idx // 2
                if proxima_luta_idx < len(lutas_novo_round):
                    luta_ant.proxima_luta = lutas_novo_round[proxima_luta_idx]
                    luta_ant.save()
            except Luta.DoesNotExist:
                pass
        
        estrutura["rounds"][round_num] = lutas_novo_round
        lutas_anteriores = lutas_novo_round
    
    return estrutura


def atualizar_proxima_luta(luta):


def calcular_pontuacao_academias(campeonato_id=None):
    """Calcula e atualiza a pontuação de todas as academias para um campeonato"""
    # Obter ou criar campeonato padrão/ativo
    if campeonato_id:
        campeonato = Campeonato.objects.filter(id=campeonato_id).first()
    else:
        campeonato = Campeonato.objects.filter(ativo=True).first()
    if not campeonato:
        campeonato = Campeonato.objects.create(nome="Campeonato Padrão", ativo=True)
    
    # Limpar pontuações anteriores deste campeonato
    AcademiaPontuacao.objects.filter(campeonato=campeonato).delete()
    
    # Mapa de pontuações por academia
    pontos_academias = {}
    
    def get_registro(academia):
        if academia.id not in pontos_academias:
            pontos_academias[academia.id] = {
                'academia': academia,
                'ouro': 0,
                'prata': 0,
                'bronze': 0,
                'quarto': 0,
                'quinto': 0,
                'festival': 0,
                'remanejamento': 0,
            }
        return pontos_academias[academia.id]
    
    for chave in chaves:
        # Sempre usar get_resultados_chave:
        # - Conta resultados reais de lutas já decididas
        # - Inclui WOs e casos de campeão automático
        resultados = get_resultados_chave(chave)
        if not resultados:
            continue
        
        # Salvar classificação no JSON da chave
        classificacao = []
        for idx, atleta_id in enumerate(resultados, 1):
            if not atleta_id:
                continue
            classificacao.append({
                "atleta_id": atleta_id,
                "colocacao": idx,
            })
        estrutura = chave.estrutura or {}
        estrutura["classificacao"] = classificacao
        chave.estrutura = estrutura
        chave.save()
        
        # Aplicar contagem por colocação
        for idx, atleta_id in enumerate(resultados, 1):
            if not atleta_id:
                continue
            try:
                atleta = Atleta.objects.get(id=atleta_id)
            except Atleta.DoesNotExist:
                continue

            reg = get_registro(atleta.academia)

            # Pontuação por colocação:
            # 1º = ouro, 2º = prata, 3º = bronze, 4º = quarto, 5º = quinto
            if idx == 1:
                reg['ouro'] += 1
            elif idx == 2:
                reg['prata'] += 1
            elif idx == 3:
                reg['bronze'] += 1
            elif idx == 4:
                reg['quarto'] += 1
            elif idx == 5:
                reg['quinto'] += 1
    
    # 3. Remanejamentos (-1 ponto por atleta remanejado)
        reg['remanejamento'] += 1
    
    # 4. Calcular pontos totais e salvar registros
    Academia.objects.all().update(pontos=0)
    for data in pontos_academias.values():
        academia = data['academia']
        ouro = data['ouro']
        prata = data['prata']
        bronze = data['bronze']
        quarto = data['quarto']
        quinto = data['quinto']
        festival = data['festival']
        remanejamento = data['remanejamento']
        
        # Regras informadas:
        # Ouro = 10, Prata = 7, Bronze = 5, 4º = 3, 5º = 1, Festival = 1
        pontos_totais = (
            ouro * 10 +
            prata * 7 +
            bronze * 5 +
            quarto * 3 +
            quinto * 1 +
            festival * 1 +
            remanejamento * (-1)
        )
        
        AcademiaPontuacao.objects.create(
            campeonato=campeonato,
            academia=academia,
            ouro=ouro,
            prata=prata,
            bronze=bronze,
            quarto=quarto,
            quinto=quinto,
            festival=festival,
            remanejamento=remanejamento,
            pontos_totais=pontos_totais,
        )
        
        academia.pontos = pontos_totais
        academia.save()


def registrar_remanejamento(inscricao_id):
    """Registra remanejamento de um atleta (inscrição) e aplica -1 ponto automaticamente"""
    try:
        atleta = Atleta.objects.get(id=inscricao_id)
    except Atleta.DoesNotExist:
        return
    
    atleta.remanejado = True
    atleta.save()
    
    # Reprocessar pontuações
    calcular_pontuacao_academias()


def get_resultados_chave(chave):
    """Retorna os resultados finais de uma chave (1º, 2º, 3º, 3º)"""
    estrutura = chave.estrutura
    
    # Lutas casadas / chave manual não contam medalhas
    if estrutura.get("tipo") in ["lutas_casadas"]:
        return []
    
    if estrutura.get("tipo") == "vazia":
        return []
    
    if estrutura.get("tipo") == "campeao_automatico":
        return [estrutura.get("vencedor")]
    
    # Melhor de 3
    if estrutura.get("tipo") == "melhor_de_3":
        lutas = Luta.objects.filter(chave=chave, round=1).order_by('id')
        if len(lutas) > 0:
            # Contar vitórias (excluindo YUKO que não é vitória)
            vitorias = {}
            for luta in lutas:
                if luta.vencedor and luta.concluida and luta.tipo_vitoria != "YUKO":
                    vencedor_id = luta.vencedor.id
                    vitorias[vencedor_id] = vitorias.get(vencedor_id, 0) + 1
            
            # Verificar se algum atleta atingiu 2 vitórias
            atletas_ids = set()
            for luta in lutas:
                if luta.atleta_a:
                    atletas_ids.add(luta.atleta_a.id)
                if luta.atleta_b:
                    atletas_ids.add(luta.atleta_b.id)
            
            vencedor_id = None
            for atleta_id, num_vitorias in vitorias.items():
                if num_vitorias >= 2:
                    vencedor_id = atleta_id
                    break
            
            if vencedor_id:
                perdedor_id = None
                for atleta_id in atletas_ids:
                    if atleta_id != vencedor_id:
                        perdedor_id = atleta_id
                        break
                if perdedor_id:
                    return [vencedor_id, perdedor_id]
        return []
    
    # Triangular
    if estrutura.get("tipo") == "triangular":
        lutas = Luta.objects.filter(chave=chave, round=1).order_by('id')
        if len(lutas) == 3:
            # Verificar se todas as lutas foram concluídas
            todas_concluidas = all(luta.concluida and luta.vencedor for luta in lutas)
            if not todas_concluidas:
                # Ainda há lutas pendentes
                return []
            
            # Contar vitórias
            vitorias = {}
            for luta in lutas:
                if luta.vencedor:
                    vencedor_id = luta.vencedor.id
                    vitorias[vencedor_id] = vitorias.get(vencedor_id, 0) + 1
            
            # Verificar se todos os atletas têm vitórias registradas
            atletas_ids = set()
            for luta in lutas:
                if luta.atleta_a:
                    atletas_ids.add(luta.atleta_a.id)
                if luta.atleta_b:
                    atletas_ids.add(luta.atleta_b.id)
            
            # Se algum atleta não tem vitória registrada, ainda não está completo
            if len(vitorias) < len(atletas_ids):
                return []
            
            # Calcular pontos técnicos por atleta
            pontos_por_atleta = {}
            ippons_por_atleta = {}
            wazaris_por_atleta = {}
            yukos_por_atleta = {}
            
            for atleta_id in atletas_ids:
                pontos_por_atleta[atleta_id] = 0
                ippons_por_atleta[atleta_id] = 0
                wazaris_por_atleta[atleta_id] = 0
                yukos_por_atleta[atleta_id] = 0
                
                for luta in lutas:
                    if luta.vencedor and luta.vencedor.id == atleta_id:
                        pontos_por_atleta[atleta_id] += luta.pontos_vencedor
                        ippons_por_atleta[atleta_id] += luta.ippon_count
                        wazaris_por_atleta[atleta_id] += luta.wazari_count
                        yukos_por_atleta[atleta_id] += luta.yuko_count
            
            # Verificar empates
            # Agrupar atletas por pontos totais
            grupos_por_pontos = {}
            for atleta_id in atletas_ids:
                pontos_total = pontos_por_atleta[atleta_id]
                if pontos_total not in grupos_por_pontos:
                    grupos_por_pontos[pontos_total] = []
                grupos_por_pontos[pontos_total].append(atleta_id)
            
            # Ordenar por pontos (maior para menor)
            ordenados_por_pontos = sorted(pontos_por_atleta.items(), key=lambda x: x[1], reverse=True)
            
            # Se há desempate manual salvo, usar ele
            if 'desempate' in estrutura:
                desempate = estrutura['desempate']
                resultados = []
                
                for pontos_total, atletas_grupo in sorted(grupos_por_pontos.items(), reverse=True):
                    if len(atletas_grupo) == 1:
                        resultados.append(atletas_grupo[0])
                    else:
                        if pontos_total in desempate:
                            resultados.extend(desempate[pontos_total])
                        else:
                            resultados.extend(atletas_grupo)
                
                return resultados[:3]
            
            # Verificar se há empate
            precisa_desempate = any(len(grupo) > 1 for grupo in grupos_por_pontos.values())
            
            if precisa_desempate:
                # Aplicar critérios de desempate
                resultados = []
                
                for pontos_total, atletas_grupo in sorted(grupos_por_pontos.items(), reverse=True):
                    if len(atletas_grupo) == 1:
                        resultados.append(atletas_grupo[0])
                    else:
                        # Desempate: 1) Vitórias, 2) Confronto direto, 3) Ippons, 4) Wazaris, 5) Yukos
                        desempatados = []
                        
                        # 1. Ordenar por número de vitórias (excluindo YUKO)
                        vitorias_grupo = {}
                        for atleta_id in atletas_grupo:
                            vitorias_grupo[atleta_id] = sum(1 for luta in lutas 
                                                          if luta.vencedor and luta.vencedor.id == atleta_id 
                                                          and luta.tipo_vitoria != "YUKO")
                        
                        ordenados_vitorias = sorted(vitorias_grupo.items(), key=lambda x: x[1], reverse=True)
                        
                        # Se ainda empatado, usar confronto direto
                        grupos_vitorias = {}
                        for atleta_id, num_vit in ordenados_vitorias:
                            if num_vit not in grupos_vitorias:
                                grupos_vitorias[num_vit] = []
                            grupos_vitorias[num_vit].append(atleta_id)
                        
                        for num_vit, atletas_vit in sorted(grupos_vitorias.items(), reverse=True):
                            if len(atletas_vit) == 1:
                                desempatados.append(atletas_vit[0])
                            else:
                                # Confronto direto
                                confrontos = []
                                for atleta_id in atletas_vit:
                                    ganhou_de = False
                                    for luta in lutas:
                                        if (luta.vencedor and luta.vencedor.id == atleta_id and
                                            ((luta.atleta_a and luta.atleta_a.id != atleta_id and luta.atleta_a.id in atletas_vit) or
                                             (luta.atleta_b and luta.atleta_b.id != atleta_id and luta.atleta_b.id in atletas_vit))):
                                            ganhou_de = True
                                            break
                                    
                                    confrontos.append((atleta_id, ganhou_de))
                                
                                confrontos.sort(key=lambda x: (not x[1], x[0]))
                                
                                # Se ainda empatado, ordenar por ippons, wazaris, yukos
                                if len([x for x in confrontos if x[1]]) > 1 or len([x for x in confrontos if not x[1]]) > 1:
                                    confrontos.sort(key=lambda x: (
                                        ippons_por_atleta[x[0]],
                                        wazaris_por_atleta[x[0]],
                                        yukos_por_atleta[x[0]]
                                    ), reverse=True)
                                
                                desempatados.extend([x[0] for x in confrontos])
                        
                        resultados.extend(desempatados)
                
                return resultados[:3]
            
            # Sem empates, retornar ordenados por pontos
            return [atleta_id for atleta_id, _ in ordenados_por_pontos[:3]]
        return []
    
    # Buscar a última luta (final)
    rounds_dict = estrutura.get("rounds", {})
    if not rounds_dict:
        return []
    
    # Converter chaves para inteiros se necessário
    rounds_keys = [int(k) for k in rounds_dict.keys() if str(k).isdigit()]
    
    if not rounds_keys:
        # Chave não finalizada
        return []
    
    ultimo_round = max(rounds_keys)
    
    if ultimo_round == 0:
        # Chave não finalizada
        return []
    
    lutas_final = Luta.objects.filter(
        chave=chave,
        round=ultimo_round
    )
    
    if len(lutas_final) == 0:
        return []
    
    luta_final = lutas_final.first()
    
    if not luta_final.vencedor:
        return []
    
    # 1º lugar
    primeiro = luta_final.vencedor.id
    
    # 2º lugar (perdedor da final)
    segundo = None
    if luta_final.atleta_a == luta_final.vencedor:
        segundo = luta_final.atleta_b.id if luta_final.atleta_b else None
    else:
        segundo = luta_final.atleta_a.id if luta_final.atleta_a else None
    
    # 3º lugares (perdedores das semifinais que não foram para a final)
    terceiros = []
    if ultimo_round > 1:
        semi_round = ultimo_round - 1
        semi_finais = Luta.objects.filter(chave=chave, round=semi_round)
        
        for semi in semi_finais:
            if semi.vencedor and semi.vencedor.id != primeiro and semi.vencedor.id != segundo:
                if semi.vencedor.id not in terceiros:
                    terceiros.append(semi.vencedor.id)
            else:
                # Perdedor da semifinal
                perdedor = None
                if semi.atleta_a and semi.atleta_a.id != (semi.vencedor.id if semi.vencedor else None):
                    perdedor = semi.atleta_a.id
                elif semi.atleta_b and semi.atleta_b.id != (semi.vencedor.id if semi.vencedor else None):
                    perdedor = semi.atleta_b.id
                
                if perdedor and perdedor not in terceiros:
                    terceiros.append(perdedor)
    
    resultados = [primeiro, segundo] + terceiros[:2]  # Máximo 2 terceiros
    return resultados
