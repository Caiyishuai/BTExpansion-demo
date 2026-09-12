(define (domain movebtob)
  (:requirements :strips)

  ;; 对应 src/bt_expansion/examples.py 的 MoveBtoB()
  ;;
  ;; 注意：手写版的后两个动作把同一文字同时放进 add 和 del_set
  ;;   Move(s,ab): add={Free(ab),WayClear}  del={Free(ab),At(s,ps)}
  ;;   Move(s,as): add={At(s,ps),WayClear}  del={Free(as),At(s,ps)}
  ;; 由于 state_transition 的定义是 (state | add) - del_set，del 会覆盖 add，
  ;; 因此这些文字实际生效的是"删除"。本文件按**实际生效语义**忠实还原，
  ;; 即把被自己 del 抵消掉的 add 项去掉。这也是适配器 ADD_DEL_CONFLICT
  ;; 检查所建议的消歧写法。

  (:predicates
    (free-ab)
    (free-as)
    (way-clear)
    (at-b-ab)
    (at-b-pb)
    (at-s-ps)
  )

  (:action move-b-to-ab
    :precondition (and (free-ab) (way-clear))
    :effect (and (at-b-ab) (not (free-ab)) (not (at-b-pb)))
    :cost 1
  )

  (:action move-s-to-ab
    :precondition (and (free-ab))
    :effect (and (way-clear) (not (free-ab)) (not (at-s-ps)))
    :cost 2
  )

  (:action move-s-to-as
    :precondition (and (free-as))
    :effect (and (way-clear) (not (free-as)) (not (at-s-ps)))
    :cost 3
  )
)
