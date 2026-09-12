(define (domain static-prune)
  (:requirements :strips :typing)

  ;; 演示「静态谓词收紧」：
  ;;   (connected ?a ?b) 描述地图拓扑，从不出现在任何动作效果中 -> 静态谓词
  ;;   适配器在 grounding 期用 :init 求值，把不连通的 move 实例直接剪掉，
  ;;   而不是生成出来再靠运行时前提去挡。
  ;;
  ;; 这类约束用 :types 表达不了（起点终点都是 location），
  ;; 只能靠静态谓词，因此是对类型收紧的必要补充。

  (:types location item)

  (:predicates
    (robot-at ?l - location)
    (connected ?from - location ?to - location)
    (item-at ?i - item ?l - location)
    (holding ?i - item)
    (hand-empty)
  )

  (:action move
    :parameters (?from - location ?to - location)
    :precondition (and (robot-at ?from) (connected ?from ?to))
    :effect (and (robot-at ?to) (not (robot-at ?from)))
    :cost 1
  )

  (:action pick
    :parameters (?i - item ?l - location)
    :precondition (and (robot-at ?l) (item-at ?i ?l) (hand-empty))
    :effect (and (holding ?i) (not (item-at ?i ?l)) (not (hand-empty)))
    :cost 1
  )

  (:action place
    :parameters (?i - item ?l - location)
    :precondition (and (robot-at ?l) (holding ?i))
    :effect (and (item-at ?i ?l) (hand-empty) (not (holding ?i)))
    :cost 1
  )
)
