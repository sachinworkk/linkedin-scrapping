urls = {
    "LAZY_LOAD_EMPLOYEE_DETAIL": 'https://www.linkedin.com/voyager/api/voyagerSearchDashLazyLoadedActions?decorationId=com.linkedin.voyager.dash.deco.search.SearchLazyLoadedActions-60&ids=List({lazyLoadingUserIds})',
    "LAZY_LOAD_COMPANY_LIST": 'https://www.linkedin.com/voyager/api/graphql?variables=(query:{companyQuery})&&queryId=voyagerSearchDashTypeahead.038b4196a88e3289bdd76d6716c2a986',
    "EMPLOYEE_DETAIL": 'https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={employeeId}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.ProfileContactInfo-11',
    "INVITATION_LINK": 'https://www.linkedin.com/voyager/api/voyagerRelationshipsDashMemberRelationships?action=verifyQuotaAndCreate&decorationId=com.linkedin.voyager.dash.deco.relationships.InvitationCreationResult-3',
    "EMPLOYEE_LIST": 'https://www.linkedin.com/voyager/api/search/dash/clusters?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-175&origin=FACETED_SEARCH&q=all&query=(flagshipSearchIntent:SEARCH_SRP,queryParameters:(currentCompany:List({companyId}),resultType:List(PEOPLE),title:List({searchQueryParams})),includeFiltersInResponse:false)&start={pageNumber}',
}
