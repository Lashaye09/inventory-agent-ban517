"""Deterministic supply-chain inventory tools. All periods must use consistent units."""
from math import sqrt, ceil
from statistics import NormalDist


def positive(**kwargs):
    for name, val in kwargs.items():
        if val is None or not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f'{name} must be a positive number')


def nonnegative(**kwargs):
    for name, val in kwargs.items():
        if val is None or not isinstance(val, (int, float)) or val < 0:
            raise ValueError(f'{name} must be a nonnegative number')


def calculate_eoq(annual_demand, order_cost, holding_cost):
    positive(annual_demand=annual_demand, order_cost=order_cost, holding_cost=holding_cost)
    q = sqrt(2*annual_demand*order_cost/holding_cost)
    return dict(model='EOQ', annual_demand=annual_demand, ordering_cost_per_order=order_cost,
                annual_holding_cost_per_unit=holding_cost, eoq=q,
                annual_ordering_cost=annual_demand/q*order_cost,
                annual_holding_cost=q/2*holding_cost,
                relevant_annual_cost=(annual_demand/q*order_cost + q/2*holding_cost),
                assumptions='Constant demand, fixed order cost, no shortages, immediate replenishment.')


def calculate_quantity_discount(annual_demand, order_cost, tiers, holding_cost=None, holding_rate=None):
    positive(annual_demand=annual_demand, order_cost=order_cost)
    if (holding_cost is None) == (holding_rate is None):
        raise ValueError('Provide either fixed holding_cost OR holding_rate (not both).')
    if holding_cost is not None: positive(holding_cost=holding_cost)
    if holding_rate is not None: positive(holding_rate=holding_rate)
    if not tiers: raise ValueError('At least one discount tier is needed')
    normalized=[]
    for tier in tiers:
        qmin, price = float(tier['min_qty']), float(tier['unit_price'])
        nonnegative(min_qty=qmin)
        positive(unit_price=price)
        normalized.append((qmin,price))
    normalized.sort()
    if normalized[0][0] > 1: raise ValueError('First tier must cover quantity 1')
    if len(set(q for q,p in normalized)) != len(normalized): raise ValueError('Duplicate tier quantity')
    candidates=[]
    for index, (qmin, price) in enumerate(normalized):
        upper = normalized[index+1][0] if index+1<len(normalized) else float('inf')
        h = holding_cost if holding_cost is not None else holding_rate*price
        eoq = sqrt(2*annual_demand*order_cost/h)
        # Evaluate unconstrained minimum when feasible, lower breakpoint, and upper-adjacent integer.
        quantities = {max(1, ceil(qmin))}
        if eoq >= qmin and eoq < upper: quantities.add(eoq)
        if upper != float('inf') and ceil(upper)-1 >= max(1,ceil(qmin)):
            quantities.add(ceil(upper)-1)
        for q in quantities:
            if q < qmin or q >= upper: continue
            total = annual_demand*price + annual_demand/q*order_cost + q/2*h
            candidates.append(dict(order_quantity=q, unit_price=price, annual_purchase_cost=annual_demand*price,
                                   annual_ordering_cost=annual_demand/q*order_cost, annual_holding_cost=q/2*h,
                                   total_annual_cost=total, holding_cost_per_unit=h))
    best=min(candidates,key=lambda x:x['total_annual_cost'])
    return dict(model='All-units quantity discount', best=best, candidates=sorted(candidates,key=lambda x:x['total_annual_cost']),
                assumptions='All-units price breaks. Compare feasible EOQs and break quantities.')


def calculate_rop(demand_per_period, lead_time, z=0, demand_std=0, lead_time_std=0):
    positive(demand_per_period=demand_per_period)
    nonnegative(lead_time=lead_time, demand_std=demand_std, lead_time_std=lead_time_std, z=z)
    sigma = sqrt(lead_time*demand_std**2 + demand_per_period**2*lead_time_std**2)
    ss = z*sigma
    return dict(model='Safety stock and reorder point', mean_lead_time_demand=demand_per_period*lead_time,
                std_lead_time_demand=sigma, safety_stock=ss, reorder_point=demand_per_period*lead_time+ss,
                assumptions='Demand and lead time independent; demand and lead-time standard deviations measured in corresponding periods.')


def calculate_periodic_review(demand_per_period, review_period, lead_time, inventory_position, z=0, demand_std=0, lead_time_std=0):
    positive(demand_per_period=demand_per_period, review_period=review_period)
    nonnegative(lead_time=lead_time, demand_std=demand_std, lead_time_std=lead_time_std, z=z)
    protection=review_period+lead_time
    sigma=sqrt(protection*demand_std**2+demand_per_period**2*lead_time_std**2)
    ss=z*sigma
    target=demand_per_period*protection+ss
    return dict(model='Fixed-period review', protection_period=protection,
                protection_period_std=sigma, safety_stock=ss, target_inventory=target,
                inventory_position=inventory_position, order_quantity=max(0,target-inventory_position),
                assumptions='Review period and lead time use the same time unit as demand; demand and lead time independent.')


def calculate_newsvendor(selling_price, unit_cost, salvage_value, mean_demand, std_demand):
    positive(selling_price=selling_price, unit_cost=unit_cost)
    nonnegative(salvage_value=salvage_value, mean_demand=mean_demand, std_demand=std_demand)
    if not salvage_value < unit_cost < selling_price: raise ValueError('Require salvage value < unit cost < selling price')
    cu=selling_price-unit_cost; co=unit_cost-salvage_value; cr=cu/(cu+co)
    q=mean_demand + NormalDist().inv_cdf(cr)*std_demand
    return dict(model='Newsvendor', underage_cost=cu, overage_cost=co, critical_ratio=cr,
                z=NormalDist().inv_cdf(cr), optimal_order_quantity=max(0,q),
                assumptions='Single period; normally distributed demand; unsold units have salvage value.')
