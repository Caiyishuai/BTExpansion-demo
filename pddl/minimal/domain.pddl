(define (domain pick-and-place)
  (:requirements :strips :typing)

  ;; 最小可运行模板：3 个动作、2 个类型、4 个谓词。
  ;; 用于展示「从 PDDL 到行为树」的最小完整闭环。

  (:types item location)

  (:predicates
    (robot-at ?l - location)
    (item-at ?i - item ?l - location)
    (holding  ?i - item)
    (hand-empty)
  )

  (:action move
    :parameters (?from - location ?to - location)
    :precondition (and (robot-at ?from))
    :effect (and (robot-at ?to) (not (robot-at ?from)))
    :cost 2
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
