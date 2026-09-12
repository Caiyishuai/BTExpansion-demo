(define (domain conditional-pick)
  (:requirements :strips :typing :negative-preconditions :conditional-effects)

  ;; 这个 domain 专门演示「分支 add」：
  ;;   在 fragile 的情况下 add broken
  ;;   在 heavy   的情况下 add tired
  ;;   两者都不成立时，只 add holding
  ;;
  ;; 目标是"拿到物体且没摔坏"，因此规划器必须主动先 reinforce
  ;; 把 fragile 去掉，才能走到不产生 broken 的那个分支。

  (:types item)

  (:predicates
    (holding ?i - item)
    (fragile ?i - item)
    (heavy ?i - item)
    (broken ?i - item)
    (tired)
    (on-table ?i - item)
  )

  (:action pick
    :parameters (?i - item)
    :precondition (and (on-table ?i))
    :effect (and
      (holding ?i)
      (not (on-table ?i))
      (when (fragile ?i) (broken ?i))
      (when (heavy ?i) (tired))
    )
    :cost 1
  )

  ;; 加固：把易碎属性去掉
  (:action reinforce
    :parameters (?i - item)
    :precondition (and (fragile ?i) (on-table ?i))
    :effect (and (not (fragile ?i)))
    :cost 2
  )

  ;; 减重：把重物属性去掉
  (:action lighten
    :parameters (?i - item)
    :precondition (and (heavy ?i) (on-table ?i))
    :effect (and (not (heavy ?i)))
    :cost 2
  )
)
