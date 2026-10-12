from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.order import Order
from app.models.campaign import Campaign
from app.models.analytics import (
    TrackingEvent,
    ConversionAttribution,
    AttributionModel,
    AttributionConfidence,
)


class AttributionService:
    @staticmethod
    async def compute_order_attribution(
        db: AsyncSession,
        order: Order,
    ) -> List[ConversionAttribution]:
        """
        Compute and persist multi-touch conversion attribution records
        (FIRST_TOUCH, LAST_TOUCH, LINEAR) for a completed order.
        """
        # 1. Check if attribution already exists for this order
        res_existing = await db.execute(
            select(ConversionAttribution).where(ConversionAttribution.order_id == order.id)
        )
        existing = res_existing.scalars().all()
        if existing:
            return list(existing)

        order_rev = float(order.total_amount)

        # 2. Look for tracking events related to this order, session or customer
        query = select(TrackingEvent).where(
            (TrackingEvent.order_id == order.id) |
            and_(
                TrackingEvent.created_at <= (order.created_at + timedelta(minutes=15)),
                (TrackingEvent.customer_id == order.customer_id if order.customer_id else False)
            )
        ).order_by(TrackingEvent.created_at.asc())

        events_res = await db.execute(query)
        events: List[TrackingEvent] = events_res.scalars().all()

        # Filter events that have campaign_id or utm_source
        touchpoint_events = [e for e in events if e.campaign_id or e.utm_source or e.channel]

        attributions_to_create: List[ConversionAttribution] = []

        if touchpoint_events:
            # Deterministic attribution from clickstream
            first_event = touchpoint_events[0]
            last_event = touchpoint_events[-1]

            first_source = f"{first_event.utm_source or first_event.channel or 'direct'} / {first_event.utm_medium or 'organic'}"
            last_source = f"{last_event.utm_source or last_event.channel or 'direct'} / {last_event.utm_medium or 'organic'}"

            # 2.1 First-Touch Model
            attr_first = ConversionAttribution(
                order_id=order.id,
                order_number=order.order_number,
                attribution_model=AttributionModel.FIRST_TOUCH.value,
                confidence=AttributionConfidence.DETERMINISTIC.value,
                first_touch_source=first_source,
                last_touch_source=last_source,
                campaign_id=first_event.campaign_id,
                campaign_code=first_event.utm_campaign,
                content_id=first_event.content_id,
                touchpoints_count=len(touchpoint_events),
                order_revenue=order_rev,
                attributed_revenue=order_rev,
                attribution_weight=1.0,
                touchpoint_details=[
                    {
                        "event_name": e.event_name,
                        "channel": e.channel,
                        "source": e.utm_source,
                        "campaign": e.utm_campaign,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in touchpoint_events
                ],
            )
            attributions_to_create.append(attr_first)

            # 2.2 Last-Touch Model
            attr_last = ConversionAttribution(
                order_id=order.id,
                order_number=order.order_number,
                attribution_model=AttributionModel.LAST_TOUCH.value,
                confidence=AttributionConfidence.DETERMINISTIC.value,
                first_touch_source=first_source,
                last_touch_source=last_source,
                campaign_id=last_event.campaign_id,
                campaign_code=last_event.utm_campaign,
                content_id=last_event.content_id,
                touchpoints_count=len(touchpoint_events),
                order_revenue=order_rev,
                attributed_revenue=order_rev,
                attribution_weight=1.0,
                touchpoint_details=attr_first.touchpoint_details,
            )
            attributions_to_create.append(attr_last)

            # 2.3 Linear Model (Divide credit among unique campaign touchpoints)
            campaign_events = [e for e in touchpoint_events if e.campaign_id]
            if campaign_events:
                weight = 1.0 / len(campaign_events)
                for ce in campaign_events:
                    attr_linear = ConversionAttribution(
                        order_id=order.id,
                        order_number=order.order_number,
                        attribution_model=AttributionModel.LINEAR.value,
                        confidence=AttributionConfidence.DETERMINISTIC.value,
                        first_touch_source=first_source,
                        last_touch_source=last_source,
                        campaign_id=ce.campaign_id,
                        campaign_code=ce.utm_campaign,
                        content_id=ce.content_id,
                        touchpoints_count=len(touchpoint_events),
                        order_revenue=order_rev,
                        attributed_revenue=round(order_rev * weight, 2),
                        attribution_weight=round(weight, 4),
                        touchpoint_details=attr_first.touchpoint_details,
                    )
                    attributions_to_create.append(attr_linear)
        else:
            # Inferred attribution via applied coupon code or campaign code
            matched_campaign: Optional[Campaign] = None
            if order.applied_promo_code:
                camp_res = await db.execute(
                    select(Campaign).where(Campaign.code == order.applied_promo_code)
                )
                matched_campaign = camp_res.scalar_one_or_none()

            conf = AttributionConfidence.INFERRED.value if (matched_campaign or order.applied_promo_code) else AttributionConfidence.UNKNOWN.value
            source_tag = f"promo_code: {order.applied_promo_code}" if order.applied_promo_code else f"channel: {order.channel}"
            inferred_rev = order_rev if (matched_campaign or order.applied_promo_code) else 0.0

            for model_name in [AttributionModel.FIRST_TOUCH.value, AttributionModel.LAST_TOUCH.value, AttributionModel.LINEAR.value]:
                attr = ConversionAttribution(
                    order_id=order.id,
                    order_number=order.order_number,
                    attribution_model=model_name,
                    confidence=conf,
                    first_touch_source=source_tag,
                    last_touch_source=source_tag,
                    campaign_id=matched_campaign.id if matched_campaign else None,
                    campaign_code=matched_campaign.code if matched_campaign else order.applied_promo_code,
                    touchpoints_count=1,
                    order_revenue=order_rev,
                    attributed_revenue=inferred_rev,
                    attribution_weight=1.0,
                    touchpoint_details=[
                        {
                            "event_name": "order_checkout",
                            "channel": order.channel,
                            "promo_code": order.applied_promo_code,
                            "confidence": conf,
                        }
                    ],
                )
                attributions_to_create.append(attr)

        for a in attributions_to_create:
            db.add(a)

        await db.commit()
        return attributions_to_create
